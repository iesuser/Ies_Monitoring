import os
import logging.config

def configure_logging(app):
    """
    Configure application logging.

    Handlers:
    - Console output for all environments
    - Rotating files for app/auth/requests
    """
    log_dir = app.config.get("LOG_DIR", os.path.join(app.config.get("BASE_DIR", "."), "logs"))
    os.makedirs(log_dir, exist_ok=True)

    log_level = app.config.get("LOG_LEVEL", "INFO").upper()
    max_bytes = int(app.config.get("LOG_MAX_BYTES", 5 * 1024 * 1024))
    backup_count = int(app.config.get("LOG_BACKUP_COUNT", 5))

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": log_level,
                    "formatter": "standard",
                },
                "app_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "filename": os.path.join(log_dir, "app.log"),
                    "maxBytes": max_bytes,
                    "backupCount": backup_count,
                    "formatter": "standard",
                    "encoding": "utf-8",
                },
                "auth_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "filename": os.path.join(log_dir, "auth.log"),
                    "maxBytes": max_bytes,
                    "backupCount": backup_count,
                    "formatter": "standard",
                    "encoding": "utf-8",
                },
                "requests_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": log_level,
                    "filename": os.path.join(log_dir, "requests.log"),
                    "maxBytes": max_bytes,
                    "backupCount": backup_count,
                    "formatter": "standard",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "app": {"handlers": ["console", "app_file"], "level": log_level, "propagate": False},
                "app.auth": {"handlers": ["console", "auth_file"], "level": log_level, "propagate": False},
                "werkzeug": {"handlers": ["console", "requests_file"], "level": log_level, "propagate": False},
            },
            "root": {"handlers": ["console"], "level": "WARNING"},
        }
    )

    app.logger.info("Logging configured. level=%s dir=%s", log_level, log_dir)
