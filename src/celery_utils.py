# src/celery_utils.py

from src import create_app
from src.celery_app import celery

flask_app = create_app()

class FlaskTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return super().__call__(*args, **kwargs)

celery.Task = FlaskTask