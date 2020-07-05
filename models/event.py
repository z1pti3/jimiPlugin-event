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
    eventFields = list()
    accuracy = float()
    impact = float()
    benign = float()
    score = float()
    uid = str()

    _dbCollection = db.db["event"]

    def bulkNew(self,bulkClass,acl,conductID,flowID,eventType,eventSubType,expiryTime,eventValues,uid,accuracy,impact,benign,score):
        self.acl = acl
        self.conductID = conductID
        self.flowID = flowID
        self.eventType = eventType
        self.eventSubType = eventSubType
        self.expiryTime = expiryTime
        self.eventValues = eventValues
        self.eventFields = list(eventValues.keys())
        self.uid = uid
        self.accuracy = accuracy
        self.impact = impact
        self.benign = benign
        self.score = score

        self.eventRaiseTime = int(time.time())

        return super(_event, self).bulkNew(bulkClass) 

    def updateRecord(self,bulkClass,eventValues,expiryTime,history=False):
        if history:
            audit._audit().add("event","history",{ "lastUpdate" : self.lastUpdateTime, "endDate" : int(time.time()), "expiryTime" : self.expiryTime, "eventValues" : self.eventValues })
        self.eventValues = eventValues
        self.eventFields = list(eventValues.keys())
        self.expiryTime = expiryTime
        if self._id != "":
            self.bulkUpdate(["eventValues","expiryTime","eventFields"],bulkClass)

