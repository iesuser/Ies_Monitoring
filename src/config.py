from dotenv import load_dotenv
import os
from os import path, sep, pardir

# Load environment variables from a custom path
load_dotenv(dotenv_path='./env')  # Adjust the path if needed

class Config:
    # Flask secret key
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    # Base directory
    BASE_DIR = path.abspath(path.dirname(__file__) + sep + pardir)
    # Templates
    TEMPLATES_FOLDERS = path.join(BASE_DIR, 'src', 'templates')
    # ShakeMap base path
    SHAKEMAP_BASE_PATH = os.getenv('SHAKEMAP_BASE_PATH', '/home/sysop/shakemap_profiles/default/data')  # default path
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Default: SQLite (local dev)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{path.join(BASE_DIR, 'db.sqlite')}"
    
    # Uncomment for production
    # AWS_MYSQL_HOST = os.getenv('AWS_MYSQL_HOST', 'default_host')
    # AWS_MYSQL_DATABASE = os.getenv('AWS_MYSQL_DATABASE', 'default_database')
    # AWS_MYSQL_USER = os.getenv('AWS_MYSQL_USER', 'default_user')
    # AWS_MYSQL_PASSWORD = os.getenv('AWS_MYSQL_PASSWORD', 'default_password')
    # MySQL connection URI
    # SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{AWS_MYSQL_USER}:{AWS_MYSQL_PASSWORD}@{AWS_MYSQL_HOST}/{AWS_MYSQL_DATABASE}'

    API_KEY = os.getenv('API_KEY', 'default_api_key')

    AUTHORIZATION = {
        'ApiKeyAuth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'Provide the internal API key for ingestion'
        }
    }

class TestConfig(Config):

    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"