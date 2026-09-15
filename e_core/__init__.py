import logging

from .celery import celery_app

__all__ = ['celery_app']

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)
logger = logging.getLogger(__name__)
