"""ShakeMap ვებ-გვერდის route-ები."""

from flask import render_template, Blueprint
from os import path

from src.config import Config

# ამ blueprint-ის template-ების საქაღალდე.
TEMPLATES_FOLDER = path.join(Config.BASE_DIR, Config.TEMPLATES_FOLDERS, "shakemap")

# Blueprint, რომელიც ShakeMap-ის HTML view-ებს მართავს.
shakemap_blueprint = Blueprint("shakemap", __name__, template_folder=TEMPLATES_FOLDER)


@shakemap_blueprint.route("/shakemap")
def shakemap():
    """ShakeMap-ის მთავარი გვერდის რენდერი."""
    return render_template("shakemap.html")

