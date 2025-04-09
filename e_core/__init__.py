import logging

from .celery import celery_app


__all__ = ['celery_app']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
