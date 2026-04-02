from flask import render_template, Blueprint, request, redirect, url_for
from os import path

from src.config import Config
from src.services import url_serializer

TEMPLATES_FOLDER = path.join(Config.BASE_DIR, "src","templates", "auth")
auth_blueprint = Blueprint("auth", __name__, template_folder=TEMPLATES_FOLDER)


@auth_blueprint.route("/login")
def auth():
    message = request.args.get('message')
    return render_template("login.html", message=message)

@auth_blueprint.route("/registration")
def registration():
    return render_template("registration.html")

@auth_blueprint.route("/reset_password/<token>")
def reset_password(token):
    uuid = url_serializer.unload_token(token=token,salt='reset_password', max_age_seconds=300)

    if uuid == 'invalid':
        return redirect(url_for('auth.auth', message=uuid))
    elif uuid == 'expired':
        return redirect(url_for('auth.auth', message=uuid))

    return render_template("resetPass.html", token=token)


@auth_blueprint.route("/change_password")
def change_password():
    return render_template("changePass.html")