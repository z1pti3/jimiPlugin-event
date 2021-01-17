from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time

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
    eventCorrelation = event._eventCorrelation().getAsClass(sessionData=api.g.sessionData,id=eventCorrelationID)[0]
    correlationMap = {}
    timeMap = []
    level = 0
    for sourceEvent, targetEvent in ((sourceEvent, targetEvent) for sourceEvent in eventCorrelation.events for targetEvent in eventCorrelation.events):
        if sourceEvent["uid"] != targetEvent["uid"]:
            for field, fieldValue in sourceEvent["eventValues"].items():
                try:
                    if type(targetEvent["eventValues"][field]) is list:
                        if fieldValue in targetEvent["eventValues"][field]:
                            mapKey = "{0}->{1}".format(sourceEvent["_id"],targetEvent["_id"])
                            if mapKey not in correlationMap:
                                correlationMap[mapKey] = { "source" : sourceEvent["_id"], "target" : targetEvent["_id"], "matches" : [], "sourceLevel" : sourceEvent["eventRaiseTime"], "targetLevel" : targetEvent["eventRaiseTime"] }
                                if sourceEvent["eventRaiseTime"] not in timeMap:
                                    timeMap.append(sourceEvent["eventRaiseTime"])
                                if targetEvent["eventRaiseTime"] not in timeMap:
                                    timeMap.append(targetEvent["eventRaiseTime"])
                            correlationMap[mapKey]["matches"].append([field,fieldValue])
                    else:
                        if fieldValue == targetEvent["eventValues"][field]:
                            mapKey = "{0}->{1}".format(sourceEvent["_id"],targetEvent["_id"])
                            if mapKey not in correlationMap:
                                correlationMap[mapKey] = { "source" : sourceEvent["_id"], "target" : targetEvent["_id"], "matches" : [] , "sourceLevel" : sourceEvent["eventRaiseTime"], "targetLevel" : targetEvent["eventRaiseTime"] }
                                if sourceEvent["eventRaiseTime"] not in timeMap:
                                    timeMap.append(sourceEvent["eventRaiseTime"])
                                if targetEvent["eventRaiseTime"] not in timeMap:
                                    timeMap.append(targetEvent["eventRaiseTime"])
                            correlationMap[mapKey]["matches"].append([field,fieldValue])
                except KeyError:
                    pass
    timeMap.sort()
    for key, item in correlationMap.items():
        item["sourceLevel"] = timeMap.index(item["sourceLevel"])*500
        item["targetLevel"] = timeMap.index(item["targetLevel"])*500

    return correlationMap, 200




