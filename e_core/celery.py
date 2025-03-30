import os
import celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_core.settings')

celery_app = celery.Celery('e_core')

celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.autodiscover_tasks()