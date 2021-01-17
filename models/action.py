import time
from netaddr import IPNetwork, IPAddress

from core import cache, helpers, static, db, logging
from core.models import action
from plugins.event.models import event

class _raiseEvent(action._action):
    eventType = str()
    eventSubType = str()
    layer = int()
    accuracy = float()
    impact = float()
    benign = float()
    history = bool()

    uid = str()
    timeToLive = float()
    eventValues = dict()

    def __init__(self):
        cache.globalCache.newCache("eventCache")
        self.bulkClass = db._bulk()

    def __del__(self):
        events = cache.globalCache.getAll("eventCache")
        popList = []
        for eventKey, eventValue in events.items():
            if eventValue["objectValue"].expiryTime < time.time():
                popList.append(eventKey)
        for popItem in popList:
            cache.globalCache.delete("eventCache",popItem)

    def postRun(self):
        self.bulkClass.bulkOperatonProcessing()

    def run(self,data,persistentData,actionResult):
        eventType = helpers.evalString(self.eventType,{"data" : data})
        eventSubType = helpers.evalString(self.eventSubType,{"data" : data})
        layer = self.layer
        accuracy = self.accuracy
        impact = self.impact
        benign = self.benign
        timeToLive = self.timeToLive
        uid = helpers.evalString(self.uid,{"data" : data})
        eventValues = helpers.evalDict(self.eventValues,{"data" : data})

        uid = "{0}-{1}-{2}".format(eventType,eventSubType,uid)

        data["var"]["event"] = {}

        if type(data["event"]) == dict:
            if "src_ip" in data["event"]:
                data["var"]["event"]["src_zone"], data["var"]["event"]["src_site"] = self.zone(data["event"]["src_ip"])
            if "dest_ip" in data["event"]:
                data["var"]["event"]["dest_zone"], data["var"]["event"]["dest_site"] = self.zone(data["event"]["dest_ip"])

        data["var"]["event"]["type"] = eventType
        data["var"]["event"]["eventSubType"] = eventSubType
        data["var"]["event"]["layer"] = layer
        data["var"]["event"]["accuracy"] = accuracy
        data["var"]["event"]["impact"] = impact
        data["var"]["event"]["benign"] = benign

        try:
            score = ((accuracy*(impact*layer))/benign)
        except ZeroDivisionError:
            score = 0
        data["var"]["event"]["score"] = score

        cacheUID = "{0}-{1}-{2}".format(data["conductID"],data["flowID"],uid)
        foundEvent = cache.globalCache.get("eventCache",cacheUID,getEvent,data["conductID"],data["flowID"],uid,eventType,eventSubType,extendCacheTime=True,customCacheTime=timeToLive,nullUpdate=True)
        if foundEvent != None:
            try:
                persistentData["plugin"]["event"].append(foundEvent)
            except:
                persistentData["plugin"]["event"] = [foundEvent]
            arrayIndex = len(persistentData["plugin"]["event"])-1
            actionResult["eventIndex"] = arrayIndex
            if foundEvent._id != "":
                if foundEvent.expiryTime > time.time():
                    changes = False
                    for key,value in eventValues.items():
                        if key in foundEvent.eventValues:
                            if value != foundEvent.eventValues[key]:
                                changes = True
                                break
                        else:
                            changes = True
                            break
                        
                    if changes:
                        foundEvent.updateRecord(self.bulkClass,eventValues,accuracy,impact,layer,benign,score,int( time.time() + timeToLive ),self.history)
                  
                        actionResult["result"] = True
                        actionResult["rc"] = 202
                        return actionResult

                    else:
                        foundEvent.expiryTime = int(time.time() + timeToLive)
                        foundEvent.bulkUpdate(["expiryTime"],self.bulkClass)

                    actionResult["result"] = True
                    actionResult["rc"] = 302
                    return actionResult
                else:
                    cache.globalCache.delete("eventCache",cacheUID)
            else:
                logging.debug("Event Update Failed - NO ID, actionID='{0}'".format(self._id),7)
                actionResult["result"] = False
                actionResult["rc"] = 500
                return actionResult
        
        eventObject = event._event().bulkNew(self.bulkClass,self.acl,data["conductID"],data["flowID"],eventType,eventSubType,int( time.time() + timeToLive ),eventValues,uid,accuracy,impact,layer,benign,score)
        cache.globalCache.insert("eventCache",cacheUID,eventObject,customCacheTime=timeToLive)
        try:
            persistentData["plugin"]["event"].append(eventObject)
        except:
            persistentData["plugin"]["event"] = [eventObject]
        arrayIndex = len(persistentData["plugin"]["event"])-1
        actionResult["eventIndex"] = arrayIndex
        actionResult["result"] = True
        actionResult["rc"] = 201
        return actionResult

    def zone(self,ip):
        sites = static.static["sites"]
        try:
            for site,addressRanges in sites.items():
                for addressRange in addressRanges:
                    if IPAddress(ip) in IPNetwork(addressRange):
                        return ("internal",site)
        except:
            pass
        return ("internet","internet")

class _eventUpdateScore(action._action):
    eventIndex = str()
    layer = int()
    accuracy = float()
    impact = float()
    benign = float()
    zeroUpdate = bool()

    def run(self,data,persistentData,actionResult):
        eventIndex = helpers.evalString(self.eventIndex,{"data" : data})
        try:
            currentEvent = persistentData["plugin"]["event"][eventIndex]
            if self.zeroUpdate:
                currentEvent.layer = self.layer
                currentEvent.accuracy = self.accuracy
                currentEvent.impact = self.impact
                currentEvent.benign = self.benign
            else:
                if self.layer > 0:
                    currentEvent.layer = self.layer
                if self.accuracy > 0:
                    currentEvent.accuracy = self.accuracy
                if self.impact > 0:
                    currentEvent.impact = self.impact
                if self.benign > 0:
                    currentEvent.benign = self.benign
            try:
                score = ((currentEvent.accuracy*(currentEvent.impact*currentEvent.layer))/currentEvent.benign)
            except ZeroDivisionError:
                score = 0
            
            currentEvent.score = score

            currentEvent.update(["layer","accuracy","impact","benign","score"])
            actionResult["result"] = True
            actionResult["rc"] = 0
            actionResult["score"] = score
        except KeyError:
            actionResult["result"] = False
            actionResult["rc"] = 404
            actionResult["msg"] = "No event found within current flow"
        return actionResult

class _eventUpdate(action._action):
    eventValues = dict()
    eventIndex = str()
    updateMode = int()

    def run(self,data,persistentData,actionResult):
        eventIndex = helpers.evalString(self.eventIndex,{"data" : data})
        eventValues = helpers.evalDict(self.eventValues,{"data" : data})
        try:
            currentEvent = persistentData["plugin"]["event"][eventIndex]
            if self.updateMode == 0:
                for key, value in eventValues.items():
                    currentEvent.eventValues[key] = value
            elif self.updateMode == 1:
                currentEvent.eventValues = eventValues
            currentEvent.update(["eventValues"])
            actionResult["result"] = True
            actionResult["rc"] = 0
        except KeyError:
            actionResult["result"] = False
            actionResult["rc"] = 404
            actionResult["msg"] = "No event found within current flow"
        return actionResult

class _eventGetCorrelations(action._action):
    correlationName = str()
    includeInactive = bool()
    excludeSingleTypes = bool()
    minScore = float()

    def run(self,data,persistentData,actionResult):
        correlationName = helpers.evalString(self.correlationName,{"data" : data})
        expiryTime = int(time.time())
        if self.includeInactive:
            expiryTime = 0
        correlatedRelationships = event._eventCorrelation().query(query={ "correlationName" : correlationName, "score" : { "$gt" : self.minScore }, "expiryTime" : { "$gt" : expiryTime } })["results"]
        if self.excludeSingleTypes:
            correlatedRelationships = [ x for x in correlatedRelationships if len(x["types"]) > 1 or len(x["subTypes"]) > 1 ]
        actionResult["result"] = True
        actionResult["rc"] = 0
        actionResult["correlations"] = correlatedRelationships
        return actionResult

class _eventBuildCorrelations(action._action):
    correlationName = str()
    expiryTime = 86400
    oldestEvent = 86400
    correlationFields = list()

    def run(self,data,persistentData,actionResult):
        correlationName = helpers.evalString(self.correlationName,{"data" : data})
        expiryTime = time.time() + self.expiryTime

        correlatedRelationships = event._eventCorrelation().getAsClass(query={ "correlationName" : correlationName, "expiryTime" : { "$gt" : int(time.time()) } })
        eventsAfterTime = int(time.time()) - self.oldestEvent
        events = event._event().getAsClass(query={ "expiryTime" : { "$gt" : eventsAfterTime }, "eventFields" : { "$in" : self.correlationFields } })
        correlatedRelationshipsUpdated = []
        correlatedRelationshipsCreated = []
        correlatedRelationshipsDeleted = []
        # Initial Pass Loop
        for eventItem in events:
            foundCorrelatedRelationship = None
            # Checking for existing relationship match
            for correlatedRelationshipItem, eventField in ((correlatedRelationshipItem, eventField) for correlatedRelationshipItem in correlatedRelationships for eventField in self.correlationFields):
                try:
                    if type(eventItem.eventValues[eventField]) is list:
                        matchFound = [ x for x in eventItem.eventValues[eventField] if x in correlatedRelationshipItem.correlations[eventField] ]
                        if len(matchFound) > 0:
                            foundCorrelatedRelationship = correlatedRelationshipItem
                            break
                    else:
                        if eventItem.eventValues[eventField] in correlatedRelationshipItem.correlations[eventField]:
                            foundCorrelatedRelationship = correlatedRelationshipItem
                            break
                except KeyError:
                    pass
            # Create new
            if foundCorrelatedRelationship == None:
                correlations = {}
                for eventField in self.correlationFields:
                    try:
                        if type(eventItem.eventValues[eventField]) is list:
                            for eventFieldItem in eventItem.eventValues[eventField]:
                                if eventField not in correlations:
                                    correlations[eventField] = []
                                if eventFieldItem not in correlations[eventField]:
                                    correlations[eventField].append(eventFieldItem)
                        else:
                            if eventField not in correlations:
                                correlations[eventField] = []
                            if eventItem.eventValues[eventField] not in correlations[eventField]:
                                correlations[eventField].append(eventItem.eventValues[eventField])
                    except KeyError:
                            pass
                newEventCorrelation = event._eventCorrelation()
                newEventCorrelation.new(self.acl, correlationName,expiryTime,[eventItem._id],[eventItem.eventType],[eventItem.eventSubType],correlations,[helpers.classToJson(eventItem,hidden=True)],eventItem.score)
                correlatedRelationships.append(newEventCorrelation)
                correlatedRelationshipsCreated.append(newEventCorrelation)
            # Merge existing
            else:
                change = False
                for eventField in self.correlationFields:
                    try:
                        if type(eventItem.eventValues[eventField]) is list:
                            for eventFieldItem in eventItem.eventValues[eventField]:
                                if eventField not in foundCorrelatedRelationship.correlations:
                                    foundCorrelatedRelationship.correlations[eventField] = []
                                if eventFieldItem not in foundCorrelatedRelationship.correlations[eventField]:
                                    foundCorrelatedRelationship.correlations[eventField].append(eventFieldItem)
                                    change = True
                        else:
                            if eventField not in foundCorrelatedRelationship.correlations:
                                foundCorrelatedRelationship.correlations[eventField] = []
                            if eventItem.eventValues[eventField] not in foundCorrelatedRelationship.correlations[eventField]:
                                foundCorrelatedRelationship.correlations[eventField].append(eventItem.eventValues[eventField])
                                change = True
                    except KeyError:
                        pass
                if eventItem._id not in foundCorrelatedRelationship.ids:
                    foundCorrelatedRelationship.ids.append(eventItem._id)
                    foundCorrelatedRelationship.events.append(helpers.classToJson(eventItem,hidden=True))
                    foundCorrelatedRelationship.score += eventItem.score
                    change = True
                if eventItem.eventType not in foundCorrelatedRelationship.types:
                    foundCorrelatedRelationship.types.append(eventItem.eventType)
                    change = True
                if eventItem.eventSubType not in foundCorrelatedRelationship.subTypes:
                    foundCorrelatedRelationship.subTypes.append(eventItem.eventSubType)
                    change = True
                if change:
                    foundCorrelatedRelationship.correlationLastUpdate = int(time.time())
                    foundCorrelatedRelationship.expiryTime = expiryTime
                    if foundCorrelatedRelationship not in correlatedRelationshipsUpdated:
                        correlatedRelationshipsUpdated.append(foundCorrelatedRelationship)
        
        # Reduction Loop
        loops = 1
        while (loops > 0):
            for currentCorrelation, correlatedRelationship in ((currentCorrelation,correlatedRelationship) for currentCorrelation in correlatedRelationships for correlatedRelationship in correlatedRelationships):
                merged = False
                if correlatedRelationship != currentCorrelation:
                    for eventField in self.correlationFields:
                        try:
                            matchFound = [ x for x in currentCorrelation.correlations[eventField] if x in correlatedRelationship.correlations[eventField] ]
                            if len(matchFound) > 0:
                                merged = True
                                break
                        except KeyError:
                            pass
                    if merged:
                        # Merging correlations
                        for eventField in self.correlationFields:
                            try:
                                for eventValue in currentCorrelation.correlations[eventField]:
                                    if eventValue not in correlatedRelationship.correlations[eventField]:
                                        correlatedRelationship.correlations[eventField].append(eventValue)
                            except KeyError:
                                pass
                        for mergeKey in ["ids","types","subTypes"]:
                            for value in getattr(currentCorrelation,mergeKey):
                                if value not in getattr(correlatedRelationship,mergeKey):
                                    getattr(correlatedRelationship,mergeKey).append(value)
                                    # Append missing events only when a new event _id is added
                                    if mergeKey == "ids":
                                        for eventItem in currentCorrelation.events:
                                            matchFound = [ x for x in correlatedRelationship.events if x["_id"] == eventItem["_id"] ]
                                            if len(matchFound) == 0:
                                                correlatedRelationship.events.append(eventItem)
                        correlatedRelationship.score += currentCorrelation.score
                        correlatedRelationship.correlationLastUpdate = int(time.time())
                        correlatedRelationship.expiryTime = expiryTime
                        if correlatedRelationship not in correlatedRelationshipsUpdated:
                            correlatedRelationshipsUpdated.append(correlatedRelationship)
                        # Deleting the eventCorrelation it was merged with
                        if currentCorrelation in correlatedRelationshipsCreated:
                            correlatedRelationshipsCreated.remove(currentCorrelation)
                        else:
                            correlatedRelationshipsDeleted.append(currentCorrelation)
                        if currentCorrelation in correlatedRelationshipsUpdated:
                            correlatedRelationshipsUpdated.remove(currentCorrelation)
                        currentCorrelation.delete()
                        correlatedRelationships.remove(currentCorrelation)
                        loops += 1
                        break
            loops -= 1

        created = [ helpers.classToJson(x,hidden=True) for x in correlatedRelationshipsCreated ]
        updated = []
        for correlatedRelationshipUpdated in correlatedRelationshipsUpdated:
            correlatedRelationshipUpdated.update(["expiryTime","ids","types","subTypes","correlations","score","events"])
            if correlatedRelationshipUpdated not in correlatedRelationshipsCreated:
                updated.append(helpers.classToJson(correlatedRelationshipUpdated,hidden=True))
        deleted = [ helpers.classToJson(x,hidden=True) for x in correlatedRelationshipsDeleted ]

        actionResult["result"] = True
        actionResult["rc"] = 0
        actionResult["correlatedEvents"] = { "created" : created, "updated" : updated, "deleted" : deleted }
        return actionResult


def getEvent(cacheUID,sessionData,conductID,flowID,uid,eventType,eventSubType):
    results = event._event().getAsClass(query={ "conductID" : conductID, "flowID" : flowID, "uid" : uid, "eventType" : eventType, "eventSubType" : eventSubType, "expiryTime" : { "$gt" : time.time() } })
    if len(results) > 0:
        return results[0]
    return None