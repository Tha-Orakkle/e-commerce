from rest_framework import serializers

# Caching mechanism for success responses
# This cache will store the dynamically created serializer classes
# to avoid creating them multiple times for the same parameters.
# This is useful for performance optimization.
# The cache is a dictionary where the key is a tuple of (message, code, data_serializer)
# and the value is the dynamically created serializer class.
_success_response_cache = {}

def get_success_response(message, code=200, data_serializer=None):
    key = (message, code, data_serializer.__class__.__name__ if data_serializer else None)
    if key in _success_response_cache:
        return _success_response_cache[key]
    
    name = f"SuccessResponse_{code}_{
        message.lower().replace(' ', '_').replace('.', '').replace('<', '').replace('>', '')
        }"
    fields = {
        'status': serializers.CharField(default='success'),
        'code': serializers.IntegerField(default=code),
        'message': serializers.CharField(default=message)
    }
    if data_serializer:
        fields['data'] = data_serializer
    
    # Dynamically create a serializer class
    _cls = type(name, (serializers.Serializer,), fields)
    _success_response_cache[key] = _cls
    return _cls



#  REFACTOR SCHEMAS
class PaginatedSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=1)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)

    
    
_success_response_schema_cache = {}

from django.utils.text import slugify
import hashlib

def make_success_schema(message, data_serializer=None, many=False, paginated=False):
    data_name = getattr(data_serializer, '__name__', 'Generic')
    slug = slugify(message)
    key_name = f"{data_name}_{slug}"
    digest = hashlib.md5(key_name.encode()).hexdigest()[:10]
    key = (data_name, digest)
    if key in _success_response_schema_cache:
        return _success_response_schema_cache[key]
    
    name = f"{data_name}Success{digest}"
    fields = {
        'status': serializers.CharField(default='success'),
        'message': serializers.CharField(default=message)
    }
    if data_serializer:
        data = data_serializer(many=True) if many else data_serializer()
        if paginated:
            P_S = type(
                f"Paginated{data_name}{digest}",
                (PaginatedSerializer,),
                {
                    'results': data_serializer(many=True)
                }
            )
            data = P_S()
        fields['data'] = data

    # Dynamically create a serializer class
    _cls = type(name, (serializers.Serializer,), fields)
    _success_response_schema_cache[key] = _cls
    return _cls
