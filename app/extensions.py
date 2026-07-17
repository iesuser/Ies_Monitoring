from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


from app.config import Config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

api = Api(
    name='IES Monitoring API',
    title='IES Monitoring API',
    version='1.0',
    description='Seismic Monitoring API',
    authorizations=Config.AUTHORIZATION,
    prefix='/api',  # API prefix
    doc='/docs', # Swagger UI path
    mask_swagger=False,  # Disable Swagger masking
    error_404_help=False  # Disable 404 help messages
)