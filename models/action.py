import time
from netaddr import IPNetwork, IPAddress

from core import cache, helpers, static
from core.models import action
from plugins.event.models import event

class _raiseEvent(action._action):
    eventType = str()
    eventSubType = str()
    layer = int()
    accuracy = float()
    impact = float()
    benign = float()

    uid = str()
    timeToLive = float()
    eventValues = dict()

    def __init__(self):
        cache.globalCache.newCache("eventCache")

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

        data["var"]["event"] = {}

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
        foundEvents = cache.globalCache.get("eventCache",cacheUID,getEvent,data["conductID"],data["flowID"],uid,eventType,eventSubType)
        if foundEvents != None and len(foundEvents) > 0:
            foundEvent = foundEvents[0]
            changes = False
            for key,value in eventValues.items():
                if key in foundEvent.eventValues:
                    if value != foundEvent.eventValues[key]:
                        changes = True
                        break
            if changes:
                foundEvent.updateRecord(eventValues,int( time.time() + timeToLive ))
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
            event._event().new(data["conductID"],data["flowID"],eventType,eventSubType,int( time.time() + timeToLive ),eventValues,uid,accuracy,impact,benign,score)
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
    return event._event().getAsClass(query={ "conductID" : conductID, "flowID" : flowID, "uid" : uid, "eventType" : eventType, "eventSubType" : eventSubType, "expiryTime" : { "$gt" : time.time() } })