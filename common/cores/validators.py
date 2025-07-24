import uuid

from common.exceptions import ErrorException


def validate_id(id, obj_name):
    """
    Validates the given id to ensure it is a valid UUID.
    """
    try:
        uuid.UUID(id)
        return True
    except Exception:
        raise ErrorException(detail=f"Invalid {obj_name} id.", code='invalid_id')
    