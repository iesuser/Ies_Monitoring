# src/logger/logging_config.py
import os
import logging.config
from logging.handlers import RotatingFileHandler


def configure_logging(app):
    os.makedirs("logs", exist_ok=True)

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "events_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/events.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "standard",
                "encoding": "utf-8",
            },
            "filters_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/filters.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "standard",
                "encoding": "utf-8",
            },
            "auth_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/auth.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "standard",
                "encoding": "utf-8",
            },
            "shakemap_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/shakemap.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 10,
                "formatter": "standard",
                "encoding": "utf-8",
            },
            "run_shakemap_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/run_shakemap.log",
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "standard",
                "encoding": "utf-8",
            },
            "requests_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/requests.log",
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 10,
                "formatter": "standard",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app.events": {"handlers": ["events_file"], "level": "INFO", "propagate": False},
            "app.filters": {"handlers": ["filters_file"], "level": "INFO", "propagate": False},
            "app.auth": {"handlers": ["auth_file"], "level": "INFO", "propagate": False},
            "app.shakemap": {"handlers": ["shakemap_file"], "level": "INFO", "propagate": False},
            "app.run_shakemap": {"handlers": ["run_shakemap_file"], "level": "INFO", "propagate": False},
            "werkzeug": {"handlers": ["requests_file"], "level": "INFO", "propagate": False},
        },
        "root": {"level": "WARNING"},
    })

