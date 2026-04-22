from datetime import timedelta

from dotenv import load_dotenv
import os
from os import path, sep, pardir

# Load environment variables from a custom path
load_dotenv(dotenv_path='.env')  # Adjust the path if needed

class Config:
    APP_ENV = os.getenv('APP_ENV', 'testing').strip().lower()
    # Flask secret key
    MY_SECRET_KEY = os.getenv('MY_SECRET_KEY', 'default_secret_key')
    # Base directory
    BASE_DIR = path.abspath(path.dirname(__file__) + sep + pardir)
    # Templates
    TEMPLATES_FOLDERS = path.join(BASE_DIR, 'src', 'templates')

    # ShakeMap base path
    SHAKEMAP_BASE_PATH = os.getenv('SHAKEMAP_BASE_PATH', f'{os.getenv("HOME")}/shakemap_profiles/default/data')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MySQL credentials
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'ies_monitoring')
    DEV_MYSQL_DATABASE = os.getenv('DEV_MYSQL_DATABASE', 'ies_monitoring_dev')
    MYSQL_USER = os.getenv('MYSQL_USER', 'ies_monitoring')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Ml_Ies_monitoring88')

    PROD_SQLALCHEMY_DATABASE_URI = os.getenv(
        'PROD_SQLALCHEMY_DATABASE_URI',
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}",
    )
    DEV_SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_SQLALCHEMY_DATABASE_URI',
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{DEV_MYSQL_DATABASE}",
    )
    TEST_SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_SQLALCHEMY_DATABASE_URI',
        f"sqlite:///{path.join(BASE_DIR, 'db.sqlite')}",
    )

    if APP_ENV == "production":
        SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", PROD_SQLALCHEMY_DATABASE_URI)
    elif APP_ENV == "development":
        SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", DEV_SQLALCHEMY_DATABASE_URI)
    elif APP_ENV == "testing":
        SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", TEST_SQLALCHEMY_DATABASE_URI)
    else:
        raise ValueError(f"Invalid database configuration for environment: {APP_ENV}")

    API_KEY = os.getenv('API_KEY', 'default_api_key')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(hours=12)
    
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

    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = os.getenv('MAIL_PORT', 587)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'your_email@gmail.com')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', 'your_password')

    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'google_maps_api_key')

class TestConfig(Config):

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"