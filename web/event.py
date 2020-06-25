from flask import Blueprint, render_template
from flask import current_app as app

from pathlib import Path
import time

from plugins.event.models import event

pluginPages = Blueprint('eventPages', __name__, template_folder="templates")

@pluginPages.route("/event/")
def mainPage():
    findActiveEvents = event._event().getAsClass(query={"expiryTime" : { "$gt" : time.time() } })
    return render_template("event.html", events=findActiveEvents)

