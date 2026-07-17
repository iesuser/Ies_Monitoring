import os
from os import path, sep, pardir
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')  # Adjust the path if needed

class Config:
    # Flask secret key
    MY_SECRET_KEY = os.getenv('MY_SECRET_KEY', 'default_secret_key')
    # Base directory
    BASE_DIR = path.abspath(path.dirname(__file__) + sep + pardir)
    # Templates
    TEMPLATES_FOLDERS = path.join(BASE_DIR, 'src', 'templates')

    AUTHORIZATION = {
        'JsonWebToken': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT token using Bearer scheme. Example: Bearer <access_token>'
        },
        'ApiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'Provide the internal API key for ingestion'
        }
    }


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'sqlite:///' + path.join(Config.BASE_DIR, 'dev.db'))


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URI', 'sqlite:///' + path.join(Config.BASE_DIR, 'prod.db'))


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
