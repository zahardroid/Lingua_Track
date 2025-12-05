"""
Celery configuration for linguatrack project.
"""
import os
import django
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguatrack.settings')

# Настраиваем Django
django.setup()

# Теперь можем импортировать настройки
from django.conf import settings

app = Celery('linguatrack')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Если используется memory broker, не пытаемся подключиться к Redis при старте
if app.conf.broker_url == 'memory://':
    import logging
    logger = logging.getLogger('celery')
    logger.info("Using memory broker (Redis not required)")

