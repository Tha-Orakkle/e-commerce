"""
Module for API responses models.
"""

class BaseAPIResponse:
    """
    BaseAPIResponse model
    """

    def __init__(self, status, code, **kwargs):
        """
        Initializes the BaseAPIREsponse.
        """
        self.status = status
        self.code = code
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def to_dict(self):
        """
        Returns dict of the object.
        """
        return self.__dict__


class SuccessAPIResponse(BaseAPIResponse):
    def __init__(self, code=200, **kwargs):
        self.status = 'success'
        super().__init__(self.status, code, **kwargs)

    
class DeleteAPIResponse(SuccessAPIResponse):
    def __init__(self, obj_name):
        super().__init__()
        self.message = f"{obj_name} deleted successfully."

class ErrorAPIResponse(BaseAPIResponse):
    def __init__(self, code=400, **kwargs):
        self.status = 'error'
        super().__init__(self.status, code, **kwargs)


class InvalidIdAPIResponse(ErrorAPIResponse):
    def __init__(self, obj_name):
        super().__init__()
        self.message = f"Invalid {obj_name} id."
