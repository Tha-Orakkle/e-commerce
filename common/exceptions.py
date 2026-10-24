from typing import Any

from rest_framework.exceptions import APIException


class ApplicationError(Exception):
    """Base exception for application-level errors."""

    def __init__(
        self,
        detail: str,
        code: str | None = None,
        status_code: str | None = None
    ):
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class ErrorException(APIException):
    """
    Handles API Exceptions.
    """
    def __init__(
        self,
        detail: str | None = None,
        code: str = 'bad_request',
        errors: dict[str, Any] | None = None,
        status_code: int = 400
    ):
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
