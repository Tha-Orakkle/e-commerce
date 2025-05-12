import uuid

from common.exceptions import ErrorException


def validate_id(id, obj_name):
    try:
        uuid.UUID(id)
        return True
    except Exception:
        raise ErrorException(detail=f"Invalid {obj_name} id.", code=400)
    

