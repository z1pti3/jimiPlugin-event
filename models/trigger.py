import time
import copy

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
        correlatedRelationships = []
        for eventItem in events:
            createNew = True
            for correlatedRelationship in correlatedRelationships:
                for eventField in self.correlationFields:
                    try:
                        if type(eventItem["eventValues"][eventField]) is list:
                            for eventFieldItem in eventItem["eventValues"][eventField]:
                                if eventFieldItem in correlatedRelationship["correlations"][eventField]:
                                    createNew = False
                                    break
                            if not createNew:
                                break
                        else:
                            if eventItem["eventValues"][eventField] in correlatedRelationship["correlations"][eventField]:
                                createNew = False
                                break
                    except KeyError:
                        pass
                if not createNew:
                    for eventField in self.correlationFields:
                        try:
                            if type(eventItem["eventValues"][eventField]) is list:
                                for eventFieldItem in eventItem["eventValues"][eventField]:
                                    if eventField not in correlatedRelationship["correlations"]:
                                        correlatedRelationship["correlations"][eventField] = []
                                    if eventFieldItem not in correlatedRelationship["correlations"][eventField]:
                                        correlatedRelationship["correlations"][eventField].append(eventFieldItem)
                            else:
                                if eventField not in correlatedRelationship["correlations"]:
                                    correlatedRelationship["correlations"][eventField] = []
                                if eventItem["eventValues"][eventField] not in correlatedRelationship["correlations"][eventField]:
                                    correlatedRelationship["correlations"][eventField].append(eventItem["eventValues"][eventField])
                        except KeyError:
                            pass
                    if eventItem["_id"] not in correlatedRelationship["ids"]:
                        correlatedRelationship["ids"].append(eventItem["_id"])
                        correlatedRelationship["score"] += eventItem["score"]
                    if eventItem["eventType"] not in correlatedRelationship["types"]:
                        correlatedRelationship["types"].append(eventItem["eventType"])
                    if eventItem["eventSubType"] not in correlatedRelationship["subTypes"]:
                        correlatedRelationship["subTypes"].append(eventItem["eventSubType"])
            if createNew:
                correlatedRelationships.append( { "ids" : [eventItem["_id"]], "types" : [eventItem["eventType"]], "subTypes" : [eventItem["eventSubType"]], "correlations" : {}, "score" : eventItem["score"]  } )
                correlatedRelationship = correlatedRelationships[-1]
                for eventField in self.correlationFields:
                    try:
                        if type(eventItem["eventValues"][eventField]) is list:
                            for eventFieldItem in eventItem["eventValues"][eventField]:
                                if eventField not in correlatedRelationship["correlations"]:
                                    correlatedRelationship["correlations"][eventField] = []
                                if eventFieldItem not in correlatedRelationship["correlations"][eventField]:
                                    correlatedRelationship["correlations"][eventField].append(eventFieldItem)
                        else:
                            if eventField not in correlatedRelationship["correlations"]:
                                correlatedRelationship["correlations"][eventField] = []
                            if eventItem["eventValues"][eventField] not in correlatedRelationship["correlations"][eventField]:
                                correlatedRelationship["correlations"][eventField].append(eventItem["eventValues"][eventField])
                    except KeyError:
                        pass

        loops = 1
        while (loops > 0):
            merged = False
            for currentCorrelation in correlatedRelationships:
                for correlatedRelationship in correlatedRelationships:
                    if correlatedRelationship != currentCorrelation:
                        for eventField in self.correlationFields:
                            try:
                                for eventValue in currentCorrelation["correlations"][eventField]:
                                    # Detecting correlations 
                                    if eventValue in correlatedRelationship["correlations"][eventField]:
                                        merged = True
                                        break
                            except KeyError:
                                pass
                            if merged:
                                break
                        if merged:
                            # Merging events
                            for eventField in self.correlationFields:
                                try:
                                    for eventValue in currentCorrelation["correlations"][eventField]:
                                        if eventValue not in correlatedRelationship["correlations"][eventField]:
                                            for eventField in self.correlationFields:
                                                for eventFieldItem in currentCorrelation["correlations"][eventField]:
                                                    if eventFieldItem not in correlatedRelationship["correlations"][eventField]:
                                                        correlatedRelationship["correlations"][eventField].append(eventFieldItem)
                                except KeyError:
                                    pass
                            for mergeKey in ["ids","types","subTypes"]:
                                for value in currentCorrelation[mergeKey]:
                                    if value not in correlatedRelationship[mergeKey]:
                                        correlatedRelationship[mergeKey].append(value)
                            correlatedRelationship["score"] += currentCorrelation["score"]
                            break
                if merged:
                    correlatedRelationships.remove(currentCorrelation)
                    loops += 1
                    break
            loops -= 1

        self.result["events"] = correlatedRelationships