from rest_framework.exceptions import APIException


class ErrorException(APIException):
    """
    Handles API Exceptions.
    """
    def __init__(self, detail=None, code='bad_request', errors=None, status_code=400):
        self.detail = detail
        self.code = code
        self.status_code = status_code
        if errors:
            self.errors = errors
        super().__init__(self.detail, self.status_code)
        
        
class InventoryDeletionError(RuntimeError):
    """
    Raised when there is an attempt to delete an Inventory instance.
    """
    pass
