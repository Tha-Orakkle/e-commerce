"""
Module for API responses models.
"""

class BaseAPIResponse:
    """
    BaseAPIResponse model
    """

    def __init__(self, **kwargs):
        """
        Initializes the BaseAPIREsponse.
        """
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)

    def to_dict(self):
        """
        Returns dict of the object.
        """
        return self.__dict__


class SuccessAPIResponse(BaseAPIResponse):
    def __init__(self, **kwargs):
        self.status = 'success'
        super().__init__(**kwargs)


class ErrorAPIResponse(BaseAPIResponse):
    def __init__(self, code=400, **kwargs):
        self.status = 'error'
        self.code = code
        super().__init__(**kwargs)
