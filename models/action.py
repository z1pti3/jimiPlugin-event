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

def getEvent(cacheUID,sessionData,conductID,flowID,uid,eventType,eventSubType):
    results = event._event().getAsClass(query={ "conductID" : conductID, "flowID" : flowID, "uid" : uid, "eventType" : eventType, "eventSubType" : eventSubType, "expiryTime" : { "$gt" : time.time() } })
    if len(results) > 0:
        return results[0]
    return None