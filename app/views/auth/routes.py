from flask import render_template, Blueprint, request, redirect, url_for

from app.config import Config
from app.utils import url_serializer

auth_blueprint = Blueprint("auth", __name__, template_folder=Config.TEMPLATES_FOLDERS + "/auth")
SUPPORTED_LANGS = {"en", "ka"}


def _normalized_lang(lang):
    if lang in SUPPORTED_LANGS:
        return lang
    return None


def _preferred_lang():
    cookie_lang = request.cookies.get("lang")
    if cookie_lang in SUPPORTED_LANGS:
        return cookie_lang
    return "en"


@auth_blueprint.route("/login")
@auth_blueprint.route("/<lang>/login")
def auth(lang=None):
    raw_lang = lang
    lang = _normalized_lang(lang)
    if raw_lang is None:
        return redirect(url_for("auth.auth", lang=_preferred_lang(), **request.args.to_dict()))
    if raw_lang is not None and lang is None:
        return redirect(url_for("auth.auth", lang="en"))

    message = request.args.get('message')
    return render_template("auth/login.html", message=message)

@auth_blueprint.route("/registration")
@auth_blueprint.route("/<lang>/registration")
def registration(lang=None):
    raw_lang = lang
    lang = _normalized_lang(lang)
    if raw_lang is None:
        return redirect(url_for("auth.registration", lang=_preferred_lang()))
    if raw_lang is not None and lang is None:
        return redirect(url_for("auth.registration", lang="en"))
    return render_template("registration.html")

@auth_blueprint.route("/reset_password/<token>")
@auth_blueprint.route("/<lang>/reset_password/<token>")
def reset_password(token, lang=None):
    raw_lang = lang
    lang = _normalized_lang(lang)
    if raw_lang is None:
        return redirect(url_for("auth.reset_password", lang=_preferred_lang(), token=token))
    if raw_lang is not None and lang is None:
        return redirect(url_for("auth.reset_password", lang="en", token=token))

    uuid = url_serializer.unload_token(token=token,salt='reset_password', max_age_seconds=300)

    if uuid == 'invalid':
        if lang:
            return redirect(url_for('auth.auth', lang=lang, message=uuid))
        return redirect(url_for('auth.auth', message=uuid))
    elif uuid == 'expired':
        if lang:
            return redirect(url_for('auth.auth', lang=lang, message=uuid))
        return redirect(url_for('auth.auth', message=uuid))

    return render_template("resetPass.html", token=token)


@auth_blueprint.route("/change_password")
@auth_blueprint.route("/<lang>/change_password")
def change_password(lang=None):
    raw_lang = lang
    lang = _normalized_lang(lang)
    if raw_lang is None:
        return redirect(url_for("auth.change_password", lang=_preferred_lang()))
    if raw_lang is not None and lang is None:
        return redirect(url_for("auth.change_password", lang="en"))
    return render_template("changePassword.html")