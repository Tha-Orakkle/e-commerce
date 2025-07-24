from rest_framework.exceptions import APIException


class ErrorException(APIException):
    """
    Handles API Exceptions.
    """
    def __init__(self, detail=None, code=400, errors=None, status_code=400):
        self.detail = detail
        if isinstance(code, int):
            self.status_code = code
        elif isinstance(code, str):
            self.status_code = status_code
            self.code = code
        if errors:
            self.errors = errors
        super().__init__(self.detail, self.status_code)
        
        

class DictValueError(ValueError):
    """
    Custom ValueError exception to accept dictionary.
    """
    def __init__(self, error_dict):
        self.error_dict = error_dict
        super().__init__(str(error_dict))