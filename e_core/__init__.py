from .celery import celery_app
import logging


__all__ = ['celery_app']

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("User module initialized.")
