from django.http import JsonResponse
from http import HTTPStatus
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotFound

from .api_responses import ErrorAPIResponse
from common.exceptions import ErrorException

ERROR_CODES = {
    status.value: status.phrase.lower().replace(" ", "_")
    for status in HTTPStatus if 400 <= status.value and status.value <= 600
}

def custom_404_handler(request, exception):
    """
    Custom 404 error handler to return a custom response format.
    To be used at django level.
    """
    return JsonResponse(
        ErrorAPIResponse(
            code=ERROR_CODES.get(404),
            message="The requested resource was not found.",
        ).to_dict(), status=404
    )

def custom_500_handler(request):
    """
    Custom 500 error handler to return a custom response format.
    To be used at django level.
    """
    return JsonResponse(
        ErrorAPIResponse(
            code=ERROR_CODES.get(500),
            message="An unexpected error occurred.",
        ).to_dict(), status=500
    )

def custom_exception_handler(exc, context):
    """
    Custom exception handler to return a custom response format.
    To be used at DRF level.
    """

    if isinstance(exc, PermissionDenied):
        return Response(
            ErrorAPIResponse(
                code=ERROR_CODES.get(403),
                message="You do not have permission to perform this action.",
            ).to_dict(), status=403
        )
    if isinstance(exc, NotFound):
        return Response(
            ErrorAPIResponse(
                code=ERROR_CODES.get(404),
                message="The requested resource was not found.",
            ).to_dict(), status=404
        )
    if isinstance(exc, ErrorException):
        error = ErrorAPIResponse(
            code=exc.code if hasattr(exc, 'code') else 'upcoming_code',
            message=exc.detail,
        )
        if hasattr(exc, 'errors') and exc.errors:
            error.errors = exc.errors
        return (Response(error.to_dict(), status=exc.status_code))
    
    
    response = exception_handler(exc, context)
    if response is not None:
        res_code = ERROR_CODES.get(response.status_code, 'unknwown')
        detail = getattr(exc, 'detail', str(exc))
        if isinstance(detail, dict):
            res_code = detail.get('code', res_code)
            detail = detail.get('message', detail)

        error_response = ErrorAPIResponse(
            code=res_code,
            message=detail
        )
        if hasattr(exc, 'errors') and exc.errors:
            error_response.errors = exc.errors
        return Response(error_response.to_dict(), status=response.status_code)
    return response