# Celery configuration will be set up here
from .celery_app import app as celery_app

__all__ = ('celery_app',)
