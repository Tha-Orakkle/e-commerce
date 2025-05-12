from rest_framework.exceptions import APIException


class ErrorException(APIException):
    def __init__(self, detail=None, code=400, errors=None):
        self.detail = detail
        self.status_code = code
        if errors:
            self.errors = errors
        super().__init__(self.detail, self.status_code)