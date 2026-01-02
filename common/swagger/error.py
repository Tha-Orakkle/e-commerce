from drf_spectacular.utils import OpenApiExample, OpenApiResponse, PolymorphicProxySerializer
from rest_framework import serializers


class ForbiddenSerializer(serializers.Serializer):
    """
    Serializer for forbidden responses.
    """
    status = serializers.CharField(default='error')
    code = serializers.IntegerField(default='permission_denied')
    message = serializers.CharField(default="You do not have permission to perform this action.")


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

def build_not_found_error_message(obj):
    return f'No {obj.lower()} matching the given ID found.'

def build_invalid_id_error(obj_name):
    return {'invalid_uuid': f'Invalid {obj_name.lower()} id.'}

def make_error_schema_response(errors, code=None):
    """
    Response schema
    Args:
        errors (dict): key - name for the error.
                       value - error message
        code: error code
    """
    
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
        ) for name, message in errors.items()]
    )

def make_error_schema_response_with_errors_field(message, errors={}):
    
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

def make_unauthorized_error_schema_response():
    errors ={
        'No token': 'Authentication credentials were not provided.',
        'Invalid token': 'Token is invalid or expired.' 
    }
    return make_error_schema_response(errors=errors, code='unauthorized_request')

def make_not_found_error_schema_response(objs):
    errors = {obj: build_not_found_error_message(obj) for obj in objs}
    return make_error_schema_response(errors=errors, code='not_found')
