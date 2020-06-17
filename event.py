from core import plugin, model

class _event(plugin._plugin):
    version = 0.1

    def install(self):
        # Register models
        model.registerModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.registerModel("event","_event","_action","plugins.event.models.event",True)
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("raiseEvent","_raiseEvent","_action","plugins.event.models.action")
        model.deregisterModel("event","_event","_action","plugins.event.models.event")
        return True

