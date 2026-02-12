"""
Celery configuration for DawaTrack Hospital.

This module configures Celery for handling asynchronous tasks like:
- Sending SMS/WhatsApp reminders
- Sending email notifications
- Generating reports
- Checking for missed doses
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dawatrack.settings')

app = Celery('dawatrack')

# Load configuration from Django settings with namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Optional: Define task base name to ensure consistency
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes hard limit
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes soft limit
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 1000
