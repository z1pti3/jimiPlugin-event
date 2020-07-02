import time
from netaddr import IPNetwork, IPAddress

from core import cache, helpers, static, db
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

    def run(self,data,persistentData,actionResult):
        if data["eventStats"]["last"]:
            self.bulkClass.bulkOperatonProcessing()

        eventType = helpers.evalString(self.eventType,{"data" : data})
        eventSubType = helpers.evalString(self.eventSubType,{"data" : data})
        layer = self.layer
        accuracy = self.accuracy
        impact = self.impact
        benign = self.benign
        timeToLive = self.timeToLive
        uid = helpers.evalString(self.uid,{"data" : data})
        eventValues = helpers.evalDict(self.eventValues,{"data" : data})

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

        score = int((accuracy*impact)*(benign/10))
        data["var"]["event"]["score"] = score

        cacheUID = "{0}-{1}-{2}-{3}-{4}".format(data["conductID"],data["flowID"],uid,eventType,eventSubType)
        foundEvent = cache.globalCache.get("eventCache",cacheUID,getEvent,data["conductID"],data["flowID"],uid,eventType,eventSubType,extendCacheTime=True,customCacheTime=timeToLive)
        if foundEvent != None:
            if foundEvent.expiryTime > time.time():
                changes = False
                for key,value in eventValues.items():
                    if key in foundEvent.eventValues:
                        if value != foundEvent.eventValues[key]:
                            changes = True
                            break
                if changes:
                    foundEvent.updateRecord(self.bulkClass,eventValues,int( time.time() + timeToLive ),self.history)
                    actionResult["result"] = True
                    actionResult["rc"] = 202
                    return actionResult

                else:
                    foundEvent.expiryTime = int(time.time() + timeToLive)
                    foundEvent.update(["expiryTime"])

                actionResult["result"] = True
                actionResult["rc"] = 302
                return actionResult
            else:
                cache.globalCache.delete("eventCache",cacheUID)
        
        eventObject = event._event().bulkNew(self.bulkClass,data["conductID"],data["flowID"],eventType,eventSubType,int( time.time() + timeToLive ),eventValues,uid,accuracy,impact,benign,score)
        cache.globalCache.insert("eventCache",cacheUID,eventObject,customCacheTime=timeToLive)
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

def getEvent(cacheUID,sessionData,conductID,flowID,uid,eventType,eventSubType):
    results = event._event().getAsClass(query={ "conductID" : conductID, "flowID" : flowID, "uid" : uid, "eventType" : eventType, "eventSubType" : eventSubType, "expiryTime" : { "$gt" : time.time() } })
    if len(results) > 0:
        return results[0]
    return None