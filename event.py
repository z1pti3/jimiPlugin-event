from core import plugin, model

class _event(plugin._plugin):
    version = 0.4

    def install(self):
        # Register models
        model.registerModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.registerModel("event","_event","_action","plugins.event.models.event",True)
        model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.deregisterModel("event","_event","_action","plugins.event.models.event")
        model.deregisterModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
        model.deregisterModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        return True

    def upgrade(self,LatestPluginVersion):
        if self.version < 0.4:
            model.registerModel("eventUpdate","_eventUpdate","_action","plugins.event.models.action")
        if self.version < 0.2:
            model.registerModel("eventThreshold","_eventThreshold","_trigger","plugins.event.models.trigger")
