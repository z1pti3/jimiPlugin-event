import time
import copy

from core import cache, helpers, static, db, logging
from core.models import trigger
from plugins.event.models import event

class _eventThreshold(trigger._trigger):
    correlationName = str()
    includeInactive = bool()
    excludeSingleTypes = bool()
    minScore = float()
    idsOnly = bool()
    summaryOnly = bool()

    def __init__(self):
        pass

    def __del__(self):
        pass

    def check(self):
        correlationName = self.correlationName
        expiryTime = int(time.time())
        if self.includeInactive:
            expiryTime = 0

        events = event._eventCorrelation().query(query={ "correlationName" : correlationName, "score" : { "$gt" : self.minScore }, "expiryTime" : { "$gt" : expiryTime } })["results"]
        if self.excludeSingleTypes:
            events = [ x for x in events if len(x["types"]) > 1 or len(x["subTypes"]) > 1 ]
        if self.summaryOnly:
            events = [  { "_id" : x["_id"], "score" : x["score"], "types" : x["types"], "subTypes" : x["subTypes"], "correlations" : x["correlations"] } for x in events ]
        if self.idsOnly:
            events = [ x["_id"] for x in events ]
        self.result["events"] = events
        