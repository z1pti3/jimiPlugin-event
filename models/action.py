import time
from netaddr import IPNetwork, IPAddress

from core import cache, helpers, static, db, logging
from core.models import action
from plugins.event.models import event

import jimi

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

    eventTitle = str()

    updateValues = bool()

    def __init__(self):
        cache.globalCache.newCache("eventCache")
        self.bulkClass = db._bulk()

    def __del__(self):
        events = []
        try:
            events = cache.globalCache.getAll("eventCache")
            popList = []
            for eventKey, eventValue in events.items():
                if eventValue["objectValue"] and eventValue["objectValue"].expiryTime < time.time():
                    popList.append(eventKey)
                elif not eventValue["objectValue"]:
                    popList.append(eventKey)
            for popItem in popList:
                cache.globalCache.delete("eventCache",popItem)
        except Exception as e:
            print(e)

    def postRun(self):
        self.bulkClass.bulkOperatonProcessing()

    def run(self,data,persistentData,actionResult):
        eventTitle = helpers.evalString(self.eventTitle,{"data" : data})
        eventType = helpers.evalString(self.eventType,{"data" : data})
        eventSubType = helpers.evalString(self.eventSubType,{"data" : data})
        layer = self.layer
        accuracy = self.accuracy
        impact = self.impact
        benign = self.benign
        timeToLive = self.timeToLive
        uid = helpers.evalString(self.uid,{"data" : data})
        eventValues = helpers.evalDict(self.eventValues,{"data" : data})

        uid = "{0}-{1}-{2}-{3}".format(self._id,eventType,eventSubType,uid)

        data["var"]["event"] = {}

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

        cacheUID = "{0}-{1}-{2}".format(data["conductID"],data["flow_id"],uid)
        foundEvent = cache.globalCache.get("eventCache",cacheUID,getEvent,data["conductID"],data["flow_id"],uid,eventType,eventSubType,extendCacheTime=True,customCacheTime=timeToLive,nullUpdate=True)
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
                        
                    if changes and self.updateValues:
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
        
        eventObject = event._event().bulkNew(self.bulkClass,self.acl,data["conductID"],data["flow_id"],eventType,eventSubType,int( time.time() + timeToLive ),eventValues,uid,accuracy,impact,layer,benign,score,data,eventTitle)
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
            elif self.updateMode == 2:
                for key, value in eventValues.items():
                    if value:
                        if key in currentEvent.eventValues:
                            if type(currentEvent.eventValues[key]) != list:
                                currentEvent.eventValues[key] = [currentEvent.eventValues[key]]
                            if type(value) is list:
                                currentEvent.eventValues[key] += value
                            else:
                                currentEvent.eventValues[key].append(value)
                        else:
                            currentEvent.eventValues[key] = value
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
    idsOnly = bool()
    summaryOnly = bool()
    multiTypeMultiplier = 1

    def run(self,data,persistentData,actionResult):
        correlationName = helpers.evalString(self.correlationName,{"data" : data})
        expiryTime = int(time.time())
        if self.includeInactive:
            expiryTime = 0
        correlatedRelationships = event._eventCorrelation().query(query={ "correlationName" : correlationName, "score" : { "$gt" : self.minScore }, "expiryTime" : { "$gt" : expiryTime } })["results"]
        if self.excludeSingleTypes:
            correlatedRelationships = [ x for x in correlatedRelationships if len(x["types"]) > 1 or len(x["subTypes"]) > 1 ]
        if self.summaryOnly:
            correlatedRelationships = [  { "_id" : x["_id"], "score" : x["score"], "types" : x["types"], "subTypes" : x["subTypes"], "correlations" : x["correlations"] } for x in correlatedRelationships ]
        if self.idsOnly:
            correlatedRelationships = [ x["_id"] for x in correlatedRelationships ]
        if self.multiTypeMultiplier > 1:
            for correlatedRelationship in correlatedRelationships:
                multiplier = ((len(correlatedRelationship["types"]) -1 + len(correlatedRelationship["subTypes"]) -1 ) * self.multiTypeMultiplier)
                if multiplier > 0:
                    correlatedRelationship["score"] = correlatedRelationship["score"] * multiplier
        actionResult["result"] = True
        actionResult["rc"] = 0
        actionResult["correlations"] = correlatedRelationships
        return actionResult

class _eventGetCorrelation(action._action):
    correlationID = str()

    def run(self,data,persistentData,actionResult):
        correlationID = helpers.evalString(self.correlationID,{"data" : data})
        correlatedRelationship = event._eventCorrelation().query(id=correlationID)["results"][0]
        actionResult["result"] = True
        actionResult["rc"] = 0
        actionResult["correlation"] = correlatedRelationship
        return actionResult

class _eventBuildCorrelations(action._action):
    correlationName = str()
    expiryTime = 86400
    oldestEvent = 86400
    correlationFields = list()
    excludeCorrelationValues = dict()
    alwaysProcessEvents = bool()
    ignoreScoreLessThan = int()

    def __init__(self):
        self.bulkClass = db._bulk()

    def run(self,data,persistentData,actionResult):
        correlationName = helpers.evalString(self.correlationName,{"data" : data})
        excludeCorrelationValues = helpers.evalDict(self.excludeCorrelationValues,{"data" : data})
        expiryTime = time.time() + self.expiryTime

        correlatedRelationships = event._eventCorrelation().getAsClass(query={ "correlationName" : correlationName, "expiryTime" : { "$gt" : int(time.time()) } })
        eventsAfterTime = int(time.time()) - self.oldestEvent
        if not self.alwaysProcessEvents:
            ids = event._eventCorrelation()._dbCollection.distinct("ids",{ "$or" : [ { "expiryTime" : { "$gt" : int(time.time()) } }, { "lastUpdateTime" : { "$gt" : eventsAfterTime } } ] })
            objectIds = []
            for idItem in ids:
                objectIds.append(db.ObjectId(idItem))
            eventSearch = { "_id" : { "$nin" : objectIds }, "expiryTime" : { "$gt" : eventsAfterTime }, "eventFields" : { "$in" : self.correlationFields } }
        else:
            eventSearch = { "expiryTime" : { "$gt" : eventsAfterTime }, "eventFields" : { "$in" : self.correlationFields } }
            
        if self.ignoreScoreLessThan > 0:
            eventSearch["score"] = { "$gt" : self.ignoreScoreLessThan }
        events = event._event().getAsClass(query=eventSearch)
        
        # Build correlation field hash table
        fields = {}
        for field in self.correlationFields:
            fields[field] = {}
            if field not in excludeCorrelationValues:
                excludeCorrelationValues[field] = []
        for correlatedRelationshipItem in correlatedRelationships:
            for field in self.correlationFields:
                try:
                    if field not in excludeCorrelationValues:
                        excludeCorrelationValues[field] = []
                    for value in correlatedRelationshipItem.correlations[field]:
                        fields[field][value] = correlatedRelationshipItem
                except KeyError:
                    pass

        correlatedRelationshipsCreated = []
        correlatedRelationshipsUpdated = []
        correlatedRelationshipsDeleted = []

        # Initial Pass Loop
        for eventItem in events:
            foundCorrelatedRelationship = None
            correlations = {}
            processNew = False
            for eventField in eventItem.eventValues:
                try:
                    if type(eventItem.eventValues[eventField]) is list:
                        correlations[eventField] = [ x for x in eventItem.eventValues[eventField] if eventField in self.correlationFields ]
                        matchFound = [ fields[eventField][x] for x in eventItem.eventValues[eventField] if eventField in self.correlationFields and x in fields[eventField] and x not in excludeCorrelationValues[eventField] ]
                        if len(matchFound) > 0:
                            foundCorrelatedRelationship = matchFound[0]
                        else:
                            matchFound = [ fields[eventField][x] for x in eventItem.eventValues[eventField] if eventField in self.correlationFields and x and x not in excludeCorrelationValues[eventField] ]
                            if len(matchFound) > 0:
                                processNew = True
                    else:
                        correlations[eventField] = [eventItem.eventValues[eventField]]
                        if eventField in self.correlationFields and eventItem.eventValues[eventField] in fields[eventField] and eventItem.eventValues[eventField] not in excludeCorrelationValues[eventField]:
                            foundCorrelatedRelationship = fields[eventField][eventItem.eventValues[eventField]]
                        else:
                            if eventField in self.correlationFields and eventItem.eventValues[eventField] and eventItem.eventValues[eventField] not in excludeCorrelationValues[eventField]:
                                processNew = True
                except KeyError:
                    pass
            # Create new
            if processNew == True:
                newEventCorrelation = event._eventCorrelation()
                newEventCorrelation.bulkNew(self.bulkClass, self.acl, correlationName,expiryTime,[eventItem._id],[eventItem.eventType],[eventItem.eventSubType],correlations,eventItem.score)
                correlatedRelationshipsCreated.append(newEventCorrelation)
                correlatedRelationships.append(newEventCorrelation)
                for eventField in eventItem.eventValues:
                    try:
                        for eventValue in correlations[eventField]:
                            try:
                                fields[eventField][eventValue] = newEventCorrelation
                            except KeyError:
                                fields[eventField] = { eventValue : newEventCorrelation }
                    except KeyError:
                        pass
            # Merge existing
            elif foundCorrelatedRelationship != None:
                for eventField in correlations:
                    try:
                        foundCorrelatedRelationship.correlations[eventField] += correlations[eventField]
                        foundCorrelatedRelationship.correlations[eventField] = list(set(foundCorrelatedRelationship.correlations[eventField]))
                    except KeyError:
                        foundCorrelatedRelationship.correlations[eventField] = correlations[eventField]
                if eventItem._id not in foundCorrelatedRelationship.ids:
                    foundCorrelatedRelationship.ids.append(eventItem._id)
                    foundCorrelatedRelationship.score += eventItem.score
                if eventItem.eventType not in foundCorrelatedRelationship.types:
                    foundCorrelatedRelationship.types.append(eventItem.eventType)
                if eventItem.eventSubType not in foundCorrelatedRelationship.subTypes:
                    foundCorrelatedRelationship.subTypes.append(eventItem.eventSubType)
                foundCorrelatedRelationship.correlationLastUpdate = int(time.time())
                foundCorrelatedRelationship.expiryTime = expiryTime
                if foundCorrelatedRelationship not in correlatedRelationshipsCreated and foundCorrelatedRelationship not in correlatedRelationshipsUpdated:
                    correlatedRelationshipsUpdated.append(foundCorrelatedRelationship)

        # Process bulk creation if needed before merging
        self.bulkClass.bulkOperatonProcessing()
  
        # Reduction Loop
        loop = 1
        maxLoops = 5
        while loop > 0 and maxLoops > 0:
            correlatedFieldsHash = {}
            for correlatedRelationship in correlatedRelationships:
                for eventField, eventValue in ((eventField, eventValue) for eventField in correlatedRelationship.correlations for eventValue in correlatedRelationship.correlations[eventField] ):
                    if eventField in self.correlationFields and eventValue not in excludeCorrelationValues[eventField]:
                        try:
                            if eventValue not in correlatedFieldsHash[eventField]:
                                correlatedFieldsHash[eventField][eventValue] = correlatedRelationship
                            else:
                                currentCorrelation = correlatedFieldsHash[eventField][eventValue]
                                for eventField in correlatedRelationship.correlations:
                                    try:
                                        currentCorrelation.correlations[eventField] += correlatedRelationship.correlations[eventField]
                                        currentCorrelation.correlations[eventField] = list(set(currentCorrelation.correlations[eventField]))
                                    except KeyError:
                                        currentCorrelation.correlations[eventField] = correlatedRelationship.correlations[eventField]
                                for mergeKey in ["ids","types","subTypes"]:
                                    for value in getattr(correlatedRelationship,mergeKey):
                                        if value not in getattr(currentCorrelation,mergeKey):
                                            getattr(currentCorrelation,mergeKey).append(value)
                                currentCorrelation.score += correlatedRelationship.score
                                currentCorrelation.correlationLastUpdate = int(time.time())
                                currentCorrelation.expiryTime = expiryTime
                                if currentCorrelation not in correlatedRelationshipsCreated and correlatedRelationship not in correlatedRelationshipsUpdated:
                                    correlatedRelationshipsUpdated.append(currentCorrelation)
                                # Deleting the eventCorrelation it was merged with
                                if correlatedRelationship not in correlatedRelationshipsDeleted:
                                    correlatedRelationshipsDeleted.append(correlatedRelationship)
                                if correlatedRelationship in correlatedRelationshipsUpdated:
                                    correlatedRelationshipsUpdated.remove(correlatedRelationship)
                                if correlatedRelationship in correlatedRelationshipsCreated:
                                    correlatedRelationshipsCreated.remove(correlatedRelationship)
                                correlatedRelationship.bulkMerge(currentCorrelation._id,self.bulkClass)
                                correlatedRelationships.remove(correlatedRelationship)
                                loop+=1
                                break
                        except KeyError:
                            correlatedFieldsHash[eventField] = { eventValue : correlatedRelationship }
            maxLoops -= 1
            loop -= 1

        created = [ helpers.classToJson(x,hidden=True) for x in correlatedRelationshipsCreated ]
        updated = [ helpers.classToJson(x,hidden=True) for x in correlatedRelationshipsUpdated ]
        deleted = [ helpers.classToJson(x,hidden=True) for x in correlatedRelationshipsDeleted ]

        for correlatedRelationshipUpdated in correlatedRelationshipsUpdated:
            correlatedRelationshipUpdated.bulkUpdate(["expiryTime","ids","types","subTypes","correlations","score"],self.bulkClass)
            updated.append(helpers.classToJson(correlatedRelationshipUpdated,hidden=True))

        self.bulkClass.bulkOperatonProcessing()

        actionResult["result"] = True
        actionResult["rc"] = 0
        actionResult["correlatedEvents"] = { "created" : created, "updated" : updated, "deleted" : deleted }
        return actionResult


def getEvent(cacheUID,sessionData,conductID,flowID,uid,eventType,eventSubType):
    results = event._event().getAsClass(query={ "conductID" : conductID, "flowID" : flowID, "uid" : uid, "eventType" : eventType, "eventSubType" : eventSubType, "expiryTime" : { "$gt" : time.time() } })
    if len(results) > 0:
        return results[0]
    return None
