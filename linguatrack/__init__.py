# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
import os

# Настраиваем Django перед импортом настроек
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguatrack.settings')

# Импортируем Celery app (он сам проверит настройки)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except Exception as e:
    # Если Celery не настроен или отключен, это нормально
    __all__ = ()

