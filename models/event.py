import time

from core import db, helpers, logging, audit

class _event(db._document):
    conductID = str()
    flowID = str()

    eventRaiseTime = float()

    eventType = str()
    eventSubType = str()
    expiryTime = int()
    eventValues = dict()
    accuracy = float()
    impact = float()
    benign = float()
    score = int()
    uid = str()

    _dbCollection = db.db["event"]

    def new(self,conductID,flowID,eventType,eventSubType,expiryTime,eventValues,uid,accuracy,impact,benign,score):
        self.conductID = conductID
        self.flowID = flowID
        self.eventType = eventType
        self.eventSubType = eventSubType
        self.expiryTime = expiryTime
        self.eventValues = eventValues
        self.uid = uid
        self.accuracy = accuracy
        self.impact = impact
        self.benign = benign
        self.score = score

        self.eventRaiseTime = int(time.time())

        return super(_event, self).new() 

    def updateRecord(self,eventValues,expiryTime):
        audit._audit().add("event","history",{ "lastUpdate" : self.lastUpdateTime, "endDate" : int(time.time()), "expiryTime" : self.expiryTime, "eventValues" : self.eventValues })
        self.eventValues = eventValues
        self.expiryTime = expiryTime
        self.update(["eventValues","expiryTime"])

