import jimi

from plugins.event.models import event

class _event(jimi.plugin._plugin):
    version = 1.31

    def install(self):
        # Register models
        jimi.jimi.model.registerModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        jimi.model.registerModel("event","_event","_document","plugins.event.models.event",True)
        jimi.model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        jimi.model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        jimi.model.registerModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        jimi.model.registerModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
        jimi.model.registerModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        jimi.model.registerModel("eventCorrelation","_eventCorrelation","_document","plugins.event.models.event",True)
        jimi.model.registerModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
        event._event()._dbCollection.create_index([("expiryTime", -1)])
        event._eventCorrelation()._dbCollection.create_index([("expiryTime", -1)])
        return True

    def uninstall(self):
        # deregister models
        jimi.model.deregisterModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        jimi.model.deregisterModel("event","_event","_document","plugins.event.models.event")
        jimi.model.deregisterModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        jimi.model.deregisterModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        jimi.model.deregisterModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        jimi.model.deregisterModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
        jimi.model.deregisterModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        jimi.model.deregisterModel("event","_eventCorrelation","_document","plugins.event.models.event")
        jimi.model.deregisterModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.5:
            jimi.model.registerModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        if self.version < 0.4:
            jimi.model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        if self.version < 0.2:
            jimi.model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        if self.version < 0.6:
            jimi.model.registerModel("eventCorrelation","_eventCorrelation","_document","plugins.event.models.event",True)
            jimi.model.registerModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
            jimi.model.registerModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        if self.version < 0.7:
            jimi.model.registerModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
        if self.version < 1.3:
            print("Creating indexes...")
            event._event()._dbCollection.create_index([("expiryTime", -1)])
            event._eventCorrelation()._dbCollection.create_index([("expiryTime", -1)])
        if self.version < 1.31:
            jimi.settings._settings().new("event",{ "icons" : {"user": "f007", "host": "f109", "event": "f05b", "src_ip": "f0ac"}})
        return True
