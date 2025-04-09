from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import PermissionDenied, NotFound

from .api_responses import ErrorAPIResponse

def custom_404_handler(request, exception):
    """
    Custom 404 error handler to return a custom response format.
    To be used at django level.
    """
    return JsonResponse(
        ErrorAPIResponse(
            code=404,
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
            code=500,
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
                code=403,
                message="You do not have permission to perform this action.",
            ).to_dict(), status=403
        )
    if isinstance(exc, NotFound):
        return Response(
            ErrorAPIResponse(
                code=404,
                message="The requested resource was not found.",
            ).to_dict(), status=404
        )
    
    response = exception_handler(exc, context)
    if response is not None:
        return Response(
            ErrorAPIResponse(
                code=response.status_code,
                message=exc.detail if hasattr(exc, 'detail') else str(exc),
            ).to_dict(), status=response.status_code
        )
    return response