from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time
import random

from core import api
from plugins.event.models import event

pluginPages = Blueprint('eventPages', __name__, template_folder="templates")

@pluginPages.route("/event/")
def mainPage():
    findActiveEvents = event._event().getAsClass(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })
    return render_template("event.html", events=findActiveEvents)

@pluginPages.route("/event/<eventID>/")
def getEvent(eventID):
    foundEvent = event._event().query(sessionData=api.g.sessionData,id=eventID)["results"][0]
    return foundEvent, 200

@pluginPages.route("/event/eventCorrelation/<eventCorrelationID>/")
def eventCorrelationPage(eventCorrelationID):
    return render_template("eventCorrelation.html")


@pluginPages.route("/event/eventCorrelation/<eventCorrelationID>/get/")
def getEventCorrelation(eventCorrelationID):
    while True:
        eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
        if eventCorrelation.mergedID != "":
            eventCorrelationID = eventCorrelation.mergedID
        else:
            break
    
    nodesDict = {}
    edgesDict = {}
    for sourceEvent in eventCorrelation.events[0:100]:
        try:
            label = sourceEvent["eventTitle"]
            if label == "":
                label = sourceEvent["uid"]
        except KeyError:
            label = sourceEvent["uid"]
        if label not in nodesDict:
            nodesDict[label] = { "id" : sourceEvent["uid"], "label" : label, "value" : 1 }
        else:
            nodesDict[label]["value"] += 1

        nodeUID = nodesDict[label]["id"]
        for field, fieldValue in sourceEvent["eventValues"].items():
            if type(fieldValue) is list:
                for fieldValueItem in fieldValue:
                    uid = "{0}={1}".format(field,fieldValueItem)
                    if uid not in nodesDict:
                        nodesDict[uid] = { "id" : uid, "label" : uid, "value" : 1 }
                    else:
                        nodesDict[uid]["value"] += 1
                    key = "{0}-{1}".format(nodeUID,uid)
                    edgesDict[key] = { "id" : key, "from" : nodeUID, "to" : uid }
            else:
                uid = "{0}={1}".format(field,fieldValue)
                if uid not in nodesDict:
                    nodesDict[uid] = { "id" : uid, "label" : uid, "value" : 1 }
                else:
                    nodesDict[uid]["value"] += 1
                key = "{0}-{1}".format(nodeUID,uid)
                edgesDict[key] = { "id" : key, "from" : nodeUID, "to" : uid }
                
    nodes = [ x for x in nodesDict.values() ]
    edges = [ x for x in edgesDict.values() ]

    return { "nodes" : nodes, "edges" : edges }, 200




