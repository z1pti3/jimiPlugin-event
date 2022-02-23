from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time
import random

from core import api
from plugins.event.models import event

import jimi
from web import ui

pluginPages = Blueprint('eventPages', __name__, template_folder="templates")

@pluginPages.route("/")
def mainPage():
    eventCount = event._event().count(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })["results"][0]["count"]
    correlationCount = event._eventCorrelation().aggregate(sessionData=api.g.sessionData,aggregateStatement=[
        { 
            "$project": {
                "_id": 1,
                "expiryTime": 1,
                "idsSize": { "$cond": { "if": { "$isArray": "$ids" }, "then": { "$size": "$ids" }, "else": 0} }
            }
        },
        {
            "$match": {
                "expiryTime" : { "$gt" : time.time() },
                "idsSize" : { "$gt" : 1 }
            }
        },
        {
            "$count" : "count"
        }
    ])
    if len(correlationCount) > 0:
        correlationCount = correlationCount[0]["count"]
    else:
        correlationCount = 0
    return render_template("home.html", activeEvents=eventCount, activeCorrelations=correlationCount)

@pluginPages.route("/activeEventsTable/<action>/")
def activeEventsTable(action):
    findActiveEvents = event._event().getAsClass(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })
    total = len(findActiveEvents)
    columns = ["id","Title","Score"]
    table = ui.table(columns,total,total)
    if action == "build":
        return table.getColumns() ,200
    elif action == "poll":
        # Custom table data so it can be vertical
        data = []
        for activeEvent in findActiveEvents:
            data.append([ui.safe(activeEvent._id),ui.dictTable(activeEvent.eventTitle),ui.dictTable(activeEvent.score)])
        table.data = data
        return { "draw" : int(jimi.api.request.args.get('draw')), "recordsTable" : 0, "recordsFiltered" : 0, "recordsTotal" : 0, "data" : data } ,200

@pluginPages.route("/activeCorrelationTable/<action>/")
def activeCorrelationTable(action):
    findActiveCorrelations = event._eventCorrelation().aggregate(sessionData=api.g.sessionData,aggregateStatement=[
        { 
            "$project": {
                "_id": 1,
                "expiryTime": 1,
                "types" : 1,
                "subTypes" : 1,
                "score" : 1,
                "idsSize": { "$cond": { "if": { "$isArray": "$ids" }, "then": { "$size": "$ids" }, "else": 0} }
            }
        },
        {
            "$match": {
                "expiryTime" : { "$gt" : time.time() },
                "idsSize" : { "$gt" : 1 }
            }
        }
    ])
    total = len(findActiveCorrelations)
    columns = ["id","Types","Sub Types","Score"]
    table = ui.table(columns,total,total)
    if action == "build":
        return table.getColumns() ,200
    elif action == "poll":
        # Custom table data so it can be vertical
        data = []
        for activeCorrelation in findActiveCorrelations:
            data.append(["<a href='/plugin/event/eventCorrelations/{0}/'>{0}</a>".format(activeCorrelation["_id"]),ui.dictTable(activeCorrelation["types"]),ui.dictTable(activeCorrelation["subTypes"]),ui.dictTable(activeCorrelation["score"])])
        table.data = data
        
        return { "draw" : int(jimi.api.request.args.get('draw')), "recordsTable" : 0, "recordsFiltered" : 0, "recordsTotal" : 0, "data" : data } ,200

@pluginPages.route("/events/")
def eventsPage():
    findActiveEvents = event._event().query(sessionData=api.g.sessionData,query={"expiryTime" : { "$gt" : time.time() } })["results"]
    return render_template("event.html", events=findActiveEvents)

@pluginPages.route("/eventCorrelations/")
def eventCorrelationsPage():
    findActiveEvents = event._eventCorrelation().aggregate(sessionData=api.g.sessionData,aggregateStatement=[
        { 
            "$project": {
                "_id": 1,
                "expiryTime": 1,
                "types" : 1,
                "subTypes" : 1,
                "score" : 1,
                "correlationName" : 1,
                "ids" : 1,
                "correlations" : 1,
                "relationships" : 1,
                "correlationLastUpdate" : 1,
                "mergedID" : 1,
                "idsSize": { "$cond": { "if": { "$isArray": "$ids" }, "then": { "$size": "$ids" }, "else": 0} }
            }
        },
        {
            "$match": {
                "expiryTime" : { "$gt" : time.time() },
                "idsSize" : { "$gt" : 1 }
            }
        }
    ])
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
            nodesDict[label] = { "id" : label, "label" : label, "value" : 1,  "icon": {"face": "'Font Awesome 6 Free'","code": "\uf780", "color": "#C72F1E", "weight":"bold"} }
        else:
            nodesDict[label]["value"] += 1

        nodeUID = nodesDict[label]["id"]
        eventSettings = jimi.settings.getSetting("event","icons")
        for field, fieldValue in sourceEvent["eventValues"].items():
            if type(fieldValue) is list:
                for fieldValueItem in fieldValue:
                    iconCode = "\uf059"
                    if field in eventSettings:
                        uid = fieldValueItem
                        iconCode = eventSettings[field]
                    else:
                        uid = "{0}={1}".format(field,fieldValueItem)
                    if uid not in nodesDict:
                        nodesDict[uid] = { "id" : uid, "label" : uid, "value" : 1, "icon": {"face": "'Font Awesome 6 Free'","code": iconCode, "color": "#1D39C4", "weight":"bold"} }
                    else:
                        nodesDict[uid]["value"] += 1
                    key = "{0}-{1}".format(nodeUID,uid)
                    edgesDict[key] = { "id" : key, "from" : nodeUID, "to" : uid }
            else:
                iconCode = "\uf059"
                if field in eventSettings:
                    uid = fieldValue
                    iconCode = eventSettings[field]
                else:
                    uid = "{0}={1}".format(field,fieldValue)
                if uid not in nodesDict:
                    nodesDict[uid] = { "id" : uid, "label" : uid, "value" : 1,"icon": {"face": "'Font Awesome 6 Free'","code": iconCode, "color": "#1D39C4", "weight":"bold"} }
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

