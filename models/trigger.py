import time

from core import cache, helpers, static, db, logging
from core.models import trigger
from plugins.event.models import event

class _eventThreshold(trigger._trigger):
    searchTime = int()
    minScore = float()
    correlationFields = list()

    def __init__(self):
        pass

    def __del__(self):
        pass

    def check(self):
        eventsAfterTime = time.time() - self.searchTime
        events = event._event().query(query={ "expiryTime" : { "$gt" : eventsAfterTime }, "eventFields" : { "$in" : self.correlationFields } },fields=["eventType","eventSubType","eventValues","eventFields","score"])["results"]
        relationshipMap = {}
        # relationshipMap pass1
        for eventItem in events:
            for eventField in self.correlationFields:
                if eventField in eventItem["eventValues"]:
                    if eventField not in relationshipMap:
                        relationshipMap[eventField] = {}
                    if eventItem["eventValues"][eventField] not in relationshipMap[eventField]:
                        relationshipMap[eventField][eventItem["eventValues"][eventField]] = { "_ids" : [], "types" : [], "subTypes" : [], "correlations" : {}, "field" : eventField, "score" : 0 }
                    if eventItem["_id"] not in relationshipMap[eventField][eventItem["eventValues"][eventField]]["_ids"]:
                        relationshipMap[eventField][eventItem["eventValues"][eventField]]["score"]+=eventItem["score"]
                        relationshipMap[eventField][eventItem["eventValues"][eventField]]["_ids"].append(eventItem["_id"])
                    if eventItem["eventType"] not in relationshipMap[eventField][eventItem["eventValues"][eventField]]["types"]:
                        relationshipMap[eventField][eventItem["eventValues"][eventField]]["types"].append(eventItem["eventType"])
                    if eventItem["eventSubType"] not in relationshipMap[eventField][eventItem["eventValues"][eventField]]["subTypes"]:
                        relationshipMap[eventField][eventItem["eventValues"][eventField]]["subTypes"].append(eventItem["eventSubType"])
                    for eventFieldKey, eventFieldValue in eventItem["eventValues"].items(): 
                        if eventFieldKey not in relationshipMap[eventField][eventItem["eventValues"][eventField]]["correlations"]:
                            relationshipMap[eventField][eventItem["eventValues"][eventField]]["correlations"][eventFieldKey] = []
                        if eventFieldValue not in relationshipMap[eventField][eventItem["eventValues"][eventField]]["correlations"][eventFieldKey]:
                            relationshipMap[eventField][eventItem["eventValues"][eventField]]["correlations"][eventFieldKey].append(eventFieldValue)
        # relationshipMap pass2 ( this needs to in future combine multiple field and corrilation types )
        correlationEvents = []
        for relationshipField in relationshipMap:
            for relationship in relationshipMap[relationshipField]:
                if relationshipMap[relationshipField][relationship]["score"]*(len(relationshipMap[relationshipField][relationship]["eventType"])+len(relationshipMap[relationshipField][relationship]["eventSubType"])) >= self.minScore:
                    correlationEvents.append({ "match" : relationship, "field" : relationshipMap[relationshipField][relationship]["field"], "score" : relationshipMap[relationshipField][relationship]["score"], "corrilationData" : relationshipMap[relationshipField][relationship] })

        self.result["events"] = correlationEvents