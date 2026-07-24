import os
from datetime import timedelta
from os import path, sep, pardir

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")


class Config:
    BASE_DIR = path.abspath(path.dirname(__file__) + sep + pardir)
    TEMPLATES_FOLDERS = path.join(BASE_DIR, "app", "templates")

    SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("MY_SECRET_KEY", "default_secret_key")
    MY_SECRET_KEY = SECRET_KEY
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    API_KEY = os.getenv("API_KEY")
    LOG_DIR = os.getenv("LOG_DIR", path.join(BASE_DIR, "logs"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))

    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_COOKIE_SECURE = False
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_REFRESH_COOKIE_PATH = "/api/auth"

    AUTHORIZATION = {
        "JsonWebToken": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "JWT token using Bearer scheme. Example: Bearer <access_token>",
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Provide the internal API key for ingestion",
        },
    }


class DevelopmentConfig(Config):
    DEBUG = True
    JWT_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DEV_DATABASE_URI",
        "sqlite:///" + path.join(Config.BASE_DIR, "dev.db"),
    )


class ProductionConfig(Config):
    DEBUG = False
    JWT_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "PROD_DATABASE_URI",
        "sqlite:///" + path.join(Config.BASE_DIR, "prod.db"),
    )


def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
