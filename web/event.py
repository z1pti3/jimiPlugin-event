from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time
import random

from core import api
from plugins.event.models import event

import jimi

pluginPages = Blueprint('eventPages', __name__, template_folder="templates")

@pluginPages.route("/")
def mainPage():
    return render_template("home.html")

@pluginPages.route("/events/")
def eventsPage():
    findActiveEvents = event._event().query(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })["results"]
    return render_template("event.html", events=findActiveEvents)

@pluginPages.route("/eventCorrelations/")
def eventCorrelationsPage():
    findActiveEvents = event._eventCorrelation().query(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() }, "$where" : "this.ids.length>1" })["results"]
    return render_template("eventCorrelations.html", eventCorrelations=findActiveEvents)

@pluginPages.route("/eventCorrelations/<eventCorrelationID>/")
def eventCorrelationPage(eventCorrelationID):
    return render_template("eventCorrelation.html")

@pluginPages.route("/eventCorrelations/<eventCorrelationID>/get/")
def getEventCorrelation(eventCorrelationID):
    while True:
        eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
        if eventCorrelation.mergedID != "":
            eventCorrelationID = eventCorrelation.mergedID
        else:
            break
    
    eventIDS = []
    for eventID in eventCorrelation.ids:
        eventIDS.append(jimi.db.ObjectId(eventID))

    events = event._event().query(sessionData=api.g.sessionData,query={ "_id" : { "$in" : eventIDS } })["results"]

    nodesDict = {}
    edgesDict = {}

    for sourceEvent in events:
        try:
            label = sourceEvent["eventTitle"]
            if label == "":
                label = sourceEvent["uid"]
        except KeyError:
            label = sourceEvent["uid"]
        if label not in nodesDict:
            nodesDict[label] = { "id" : label, "label" : label, "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } }
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

@pluginPages.route("/eventCorrelations/<eventCorrelationID>/getTimeline/")
def getEventCorrelationTimeline(eventCorrelationID):
    while True:
        eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
        if eventCorrelation.mergedID != "":
            eventCorrelationID = eventCorrelation.mergedID
        else:
            break
    
    eventIDS = []
    for eventID in eventCorrelation.ids:
        eventIDS.append(jimi.db.ObjectId(eventID))

    events = event._event().query(sessionData=api.g.sessionData,query={ "_id" : { "$in" : eventIDS } })["results"]

    timeline = []

    for sourceEvent in events:
        try:
            label = sourceEvent["eventTitle"]
            if label == "":
                label = sourceEvent["uid"]
        except KeyError:
            label = sourceEvent["uid"]
        formatted_date = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(sourceEvent["eventRaiseTime"]))
        timeline.append({ "id" : len(timeline), "content" : label, "start" : formatted_date })

    return { "results" : timeline }, 200

@pluginPages.route("/eventCorrelations/<eventCorrelationID>/close/")
def getEvent(eventCorrelationID):
    while True:
        eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
        if eventCorrelation.mergedID != "":
            eventCorrelationID = eventCorrelation.mergedID
        else:
            break
    eventCorrelation.expiryTime = 0
    eventCorrelation.update(["expiryTime"],sessionData=api.g.sessionData)
    return { }, 200

@pluginPages.route("/eventCorrelations/<eventCorrelationID>/events/<eventUID>/")
def closeCorrelation(eventCorrelationID,eventUID):
    while True:
        eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
        if eventCorrelation.mergedID != "":
            eventCorrelationID = eventCorrelation.mergedID
        else:
            break
    
    eventIDS = []
    for eventID in eventCorrelation.ids:
        eventIDS.append(jimi.db.ObjectId(eventID))

    events = event._event().query(sessionData=api.g.sessionData,query={ "_id" : { "$in" : eventIDS }, "uid" : eventUID })
    return events, 200

