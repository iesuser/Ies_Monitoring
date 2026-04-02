from flask import render_template, Blueprint
from os import path

from src.config import Config

TEMPLATES_FOLDER = path.join(Config.BASE_DIR, "src","templates", "accounts")
accounts_blueprint = Blueprint("accounts", __name__, template_folder=TEMPLATES_FOLDER)


@accounts_blueprint.route("/accounts")
def accounts():
    return render_template("accounts.html")