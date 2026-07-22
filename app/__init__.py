from flask import Flask, render_template

from app.config import get_config

from app.extensions import db, migrate, jwt, api as restx_api
from app import api as api_package # ensure namespaces are imported

# Register blueprints
BLUEPRINTS = []
COMMANDS = []


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    @app.route("/")
    def home():
        return render_template("index.html")
    
    register_extensions(app)

    # Register error handlers
    register_error_handlers(app)

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