from drf_spectacular.utils import OpenApiExample, OpenApiResponse, PolymorphicProxySerializer
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


unauthorized_errors ={
    'No token': 'Authentication credentials were not provided.',
    'Invalid token': 'Token is invalid or expired.' 
}


def get_error_response_with_examples(examples=unauthorized_errors, code=None):
    return OpenApiResponse(
        response={
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'code': {'type': 'string', 'example': code},
                'message': {'type': 'string'}
            },
            'required': ['status', 'code', 'message']
        },
        description='Error',
        examples=[OpenApiExample(
            name.replace(".", "").replace("_", " ").capitalize(),
            value={
                'status': 'error',
                'code': code if code else name,
                'message': message
            }
        ) for name, message in examples.items()]
    )


def get_error_response_for_post_requests(message, errors={}):
    
    return OpenApiResponse(
        response={
            'type': 'object',
            'properties': {
                'status': {'type': 'string', 'example': 'error'},
                'code': {'type': 'string', 'example': ''},
                'message': {'type': 'string'},
                'errors': {
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            },
            'required': ['status', 'code', 'message']
        },
        description='Error',
        examples=[OpenApiExample(
            ' '.join(code.split('_')).capitalize(),
            value={
                'status': 'error',
                'code': code,
                'message': message,
                'errors': {
                    k: v for k, v in errors[code].items()
                }
            }
        ) for code in errors.keys()]
    )


# ERROR SERIALIZERS FOR SWAGGER UI

class ForbiddenSerializer(serializers.Serializer):
    """
    Serializer for forbidden responses.
    """
    status = serializers.CharField(default='error')
    code = serializers.IntegerField(default='permission_denied')
    message = serializers.CharField(default="You do not have permission to perform this action.")



# REFACTORS BELOW

class BaseErrorSerializer(serializers.Serializer):
    status = serializers.CharField(default='error', read_only=True)
    code = serializers.ChoiceField(choices=[
        'not_found', 'validation_error', 'permission_denied'])
    message = serializers.CharField()
    
    
class ErrorDetailsSerializer(BaseErrorSerializer):
    """
    Serializer for detailed error responses.
    """
    errors = serializers.DictField(child=serializers.ListField(
        child=serializers.CharField()), required=False)
    

# for polymorphic proxy serializer (400 bad request)
polymorphic_response = PolymorphicProxySerializer(
    component_name='APIError',
    serializers=[BaseErrorSerializer, ErrorDetailsSerializer],
    resource_type_field_name=None
)

def build_error_schema_examples(errors):
    return [OpenApiExample(
        name=' '.join(code.split('_')).capitalize(),
        value={
            'status': 'error',
            'code': code,
            'message': message
        }
    ) for code, message in errors.items()]


def build_error_schema_examples_with_errors_field(message, errors={}):
    return [OpenApiExample(
        name=' '.join(code.split('_')).capitalize(),
        value={
            'status': 'error',
            'code': code,
            'message': message,
            'errors': {
                k: v for k, v in errors[code].items()
            }
        }
    ) for code in errors.keys()]

# ===================================


# for bad request errors 400 (necessary where errors wont be one_of)
def make_error_schema_response(errors, code=None):
    """
    Response schema for bad requests.
    Args:
        errors (dict): key - name for the error.
                       value - error message
        code: error code
    """
    return get_error_response_with_examples(examples=errors, code=code)
    
def make_error_schema_response_with_errors_field(errors, message):
    return get_error_response_for_post_requests(message=message, errors=errors)

# for unauthorized errors 401
def make_unauthorized_error_schema_response():
    errors ={
        'No token': 'Authentication credentials were not provided.',
        'Invalid token': 'Token is invalid or expired.' 
    }
    return get_error_response_with_examples(examples=errors, code='unauthorized_request')


# for forbidden request 403
def make_forbidden_error_schema_response():
    return ForbiddenSerializer


# for not found errors 404
def build_not_found_error_message(obj):
    return f'No {obj.lower()} matching the given id found.'

def make_not_found_error_schema_response(objs):
    errors = {obj: build_not_found_error_message(obj) for obj in objs}
    return get_error_response_with_examples(examples=errors, code='not_found')

def build_invalid_id_error(obj_name):
    return {'invalid_uuid': f'Invalid {obj_name.lower()} id.'}
