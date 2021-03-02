import time

from core import db, helpers, logging, audit

class _eventCorrelation(db._document):
    correlationName = str()
    ids = list()
    types = list()
    subTypes = list()
    correlations = dict()
    relationships = list()
    score = float()
    correlationLastUpdate = int()
    expiryTime = int()
    mergedID = str()

    _dbCollection = db.db["eventCorrelation"]

    def new(self,acl,correlationName,expiryTime,ids,types,subTypes,correlations,score):
        self.acl = acl
        self.correlationName = correlationName
        self.expiryTime = int(time.time()) + expiryTime
        self.ids = ids
        self.types = types
        self.subTypes = subTypes
        self.correlations = correlations
        self.score = score
        self.correlationLastUpdate = int(time.time())
        return super(_eventCorrelation, self).new()

    def bulkNew(self,bulkClass,acl,correlationName,expiryTime,ids,types,subTypes,correlations,score):
        self.acl = acl
        self.correlationName = correlationName
        self.expiryTime = int(time.time()) + expiryTime
        self.ids = ids
        self.types = types
        self.subTypes = subTypes
        self.correlations = correlations
        self.score = score
        self.correlationLastUpdate = int(time.time())
        return super(_eventCorrelation, self).bulkNew(bulkClass)

    def merge(self,mergedID):
        self.mergedID = mergedID
        self.correlationName = mergedID
        self.expiryTime = 0
        self.ids = []
        self.types = []
        self.subTypes = []
        self.correlations = []
        self.score = 0
        self.correlationLastUpdate = 0
        self.update(["mergedID","correlationName","expiryTime","ids","types","subTypes","correlations","score","correlationLastUpdate"])

    def bulkMerge(self,mergedID,bulkClass):
        self.mergedID = mergedID
        self.correlationName = mergedID
        self.expiryTime = 0
        self.ids = []
        self.types = []
        self.subTypes = []
        self.correlations = []
        self.score = 0
        self.correlationLastUpdate = 0
        self.bulkUpdate(["mergedID","correlationName","expiryTime","ids","types","subTypes","correlations","score","correlationLastUpdate"],bulkClass)    


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
    layer = float()
    benign = float()
    score = float()
    uid = str()
    data = dict()
    eventTitle = str()

    _dbCollection = db.db["event"]

    def bulkNew(self,bulkClass,acl,conductID,flowID,eventType,eventSubType,expiryTime,eventValues,uid,accuracy,impact,layer,benign,score,data,eventTitle):
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
        self.layer = layer
        self.benign = benign
        self.score = score
        self.data = data
        self.eventTitle = eventTitle

        self.eventRaiseTime = int(time.time())

        return super(_event, self).bulkNew(bulkClass) 

    def updateRecord(self,bulkClass,eventValues,accuracy,impact,layer,benign,score,expiryTime,history=False):
        if history:
            audit._audit().add("event","history",{ "lastUpdate" : self.lastUpdateTime, "endDate" : int(time.time()), "expiryTime" : self.expiryTime, "eventValues" : self.eventValues, "accuracy" : self.accuracy, "impact" : self.impact, "layer" : self.layer, "score" : self.score })
        self.eventValues = eventValues
        self.eventFields = list(eventValues.keys())
        self.expiryTime = expiryTime
        self.accuracy = accuracy
        self.impact = impact
        self.layer = layer
        self.benign = benign
        self.score = score
        if self._id != "":
            self.bulkUpdate(["eventValues","expiryTime","eventFields","accuracy","impact","layer","benign","score"],bulkClass)

