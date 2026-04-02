from flask import render_template, Blueprint
from os import path

from src.config import Config

TEMPLATES_FOLDER = path.join(Config.BASE_DIR, "src", "templates", "events")
events_blueprint = Blueprint("events", __name__, template_folder=TEMPLATES_FOLDER)


@events_blueprint.route("/events")
def events():
    return render_template("events.html")
