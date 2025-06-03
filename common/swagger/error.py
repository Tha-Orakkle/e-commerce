from drf_spectacular.utils import OpenApiExample, OpenApiResponse
from rest_framework import serializers

# Caching mechanism for error responses
# This cache will store the dynamically created serializer classes
# to avoid creating them multiple times for the same parameters.
# This is useful for performance optimization.
# The cache is a dictionary where the key is a tuple of (message, code, error_serializer)
# and the value is the dynamically created serializer class.
_error_response_cache = {}


def get_error_response(message, code=400, error_serializer=None):
    key = (message, code, error_serializer.__class__.__name__ if error_serializer else None)
    if key in _error_response_cache:
        return _error_response_cache[key]
    name = f"ErrorResponse_{code}_{
        message.lower().replace(' ', '_').replace('.', '').replace('\n',  '')}"
    fields = {
        'status': serializers.CharField(default='error'),
        'code': serializers.IntegerField(default=code),
        'message': serializers.CharField(default=message)
    }
    if error_serializer:
        fields['errors'] = error_serializer

    # Dynamically create a serializer class
    _cls = type(name, (serializers.Serializer,), fields)
    _error_response_cache[key] = _cls
    return _cls


get_error_response_with_examples = lambda examples_dict, code=400: OpenApiResponse(
    response={'type': 'object'},
    examples=[OpenApiExample(
        name,
        value={
            'status': 'error',
            'code': code,
            'message': message
        }
    ) for name, message in examples_dict.items()]
)



# ERROR SERIALIZERS FOR SWAGGER UI
class BaseErrorSerializer(serializers.Serializer):
    """
    Base class for error serializers.
    """
    status = serializers.CharField(default='error')


class UnauthorizedSerializer(BaseErrorSerializer):
    """
    Serializer for unauthorized responses.
    """
    code = serializers.IntegerField(default=401)
    message = serializers.ChoiceField(
        choices=[
            "Authentication credentials were not provided.",
            "Token is invalid or expired."
        ],
        help_text="One of the predefined authentication error messages."
    )
    

class ForbiddenSerializer(BaseErrorSerializer):
    """
    Serializer for forbidden responses.
    """
    code = serializers.IntegerField(default=403)
    message = serializers.CharField(default="You do not have permission to perform this action.")
