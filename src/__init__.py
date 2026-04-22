from flask import Flask, render_template
from flask_cors import CORS

from src.config import Config
from src.commands import init_db, populate_db
from src.extensions import db, migrate, jwt, api as restx_api
from src.logger import configure_logging
from src.models import User
from src.views import shakemap_blueprint, auth_blueprint, accounts_blueprint, events_blueprint
from src import api as api_package # ensure namespaces are imported

# Register blueprints
BLUEPRINTS = [shakemap_blueprint, auth_blueprint, accounts_blueprint, events_blueprint]
COMMANDS = [init_db, populate_db]


def create_app(config=Config):
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)
    configure_logging(app)

    @app.route("/")
    def home():
        return render_template("index.html")

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    # Register error handlers
    register_error_handlers(app)

    return app

def register_extensions(app):
    """Initialize Flask extensions."""

    # Flask-SQLAlchemy
    db.init_app(app)

    # Flask-Migrate
    migrate.init_app(app, db)

    # Flask-RESTX (attach namespaces defined in src/api)
    restx_api.init_app(app)

    # Flask-JWT-Extended
    jwt.init_app(app)

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        try:
            return user.uuid
        except AttributeError:
            return user
        
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        user_uuid = jwt_data.get("sub")
        # print(f"JWT Data: {jwt_data}")
        if user_uuid:
            user = User.query.filter_by(uuid=user_uuid).first()
            return user
        return None

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