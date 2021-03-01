from core import plugin, model

class _event(plugin._plugin):
    version = 1.03

    def install(self):
        # Register models
        model.registerModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.registerModel("event","_event","_document","plugins.event.models.event",True)
        model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        model.registerModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        model.registerModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
        model.registerModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        model.registerModel("eventCorrelation","_eventCorrelation","_document","plugins.event.models.event",True)
        model.registerModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.deregisterModel("event","_event","_document","plugins.event.models.event")
        model.deregisterModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        model.deregisterModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        model.deregisterModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        model.deregisterModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
        model.deregisterModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        model.deregisterModel("event","_eventCorrelation","_document","plugins.event.models.event")
        model.deregisterModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.5:
            model.registerModel("eventUpdateScore","_eventUpdateScore","_action","plugins.event.models.action")
        if self.version < 0.4:
            model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        if self.version < 0.2:
            model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        if self.version < 0.6:
            model.registerModel("eventCorrelation","_eventCorrelation","_document","plugins.event.models.event",True)
            model.registerModel("eventGetCorrelations","_eventGetCorrelations","_action","plugins.event.models.action")
            model.registerModel("eventBuildCorrelations","_eventBuildCorrelations","_action","plugins.event.models.action")
        if self.version < 0.7:
            model.registerModel("eventGetCorrelation","_eventGetCorrelation","_action","plugins.event.models.action")
