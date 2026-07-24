from flask import Flask, g, redirect, render_template, request, url_for

from app.config import get_config
from app.commands import init_db, populate_db
from app.views import auth_blueprint
from app.extensions import db, migrate, jwt, api as restx_api
from app.logger import configure_logging
from app import api as api_package # ensure namespaces are imported

# Register blueprints
BLUEPRINTS = [auth_blueprint]
COMMANDS = [init_db, populate_db]
SUPPORTED_LANGS = {"en", "ka"}
DEFAULT_LANG = "en"


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())
    configure_logging(app)

    @app.route("/")
    def home():
        preferred = request.cookies.get("lang")
        if preferred not in SUPPORTED_LANGS:
            preferred = DEFAULT_LANG
        return redirect(url_for("home_localized", lang=preferred))

    @app.route("/<lang>/")
    def home_localized(lang):
        if lang not in SUPPORTED_LANGS:
            return redirect(url_for("home_localized", lang=DEFAULT_LANG))
        g.current_lang = lang
        response = render_template("index.html")
        return response
    
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    # Register error handlers
    register_error_handlers(app)
    register_i18n_helpers(app)

    return app

def register_extensions(app):
    """Initialize Flask extensions."""
    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Migrate
    migrate.init_app(app, db)

    # Flask-RESTX (attach namespaces defined in app/api)
    restx_api.init_app(app)

    # Flask-JWT-Extended
    jwt.init_app(app)
    register_jwt_callbacks()


def register_jwt_callbacks():
    """Wire JWT identity lookup to the User model."""

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from app.models import User

        identity = jwt_data.get("sub")
        if not identity:
            return None
        return User.query.filter_by(uuid=identity, is_active=True).first()

def register_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

def register_commands(app):
    for command in COMMANDS:
        app.cli.add_command(command)


def register_i18n_helpers(app):
    @app.before_request
    def set_current_language():
        maybe_lang = request.view_args.get("lang") if request.view_args else None
        cookie_lang = request.cookies.get("lang")

        if maybe_lang in SUPPORTED_LANGS:
            g.current_lang = maybe_lang
            g.persist_lang_cookie = True
            return

        if cookie_lang in SUPPORTED_LANGS:
            g.current_lang = cookie_lang
            g.persist_lang_cookie = False
            return

        g.current_lang = DEFAULT_LANG
        g.persist_lang_cookie = False

    @app.context_processor
    def inject_i18n_context():
        return {
            "current_lang": getattr(g, "current_lang", DEFAULT_LANG),
            "supported_langs": sorted(SUPPORTED_LANGS),
        }

    @app.after_request
    def persist_language_cookie(response):
        # Persist language only for explicit localized URLs like /en/... or /ka/...
        # so API and non-localized routes do not accidentally overwrite user preference.
        if getattr(g, "persist_lang_cookie", False):
            lang = getattr(g, "current_lang", DEFAULT_LANG)
            response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
        return response

# Custom error handler for 404
def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        # You can return a JSON response or render a custom HTML template
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        app.logger.exception('An exception occurred during a request.')
        return render_template("500.html"), 500