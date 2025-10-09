from django.utils.text import slugify
import hashlib
from rest_framework import serializers


#  SUCCESS SCHEMAS
class PaginatedSerializer(serializers.Serializer):
    count = serializers.IntegerField(default=1)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)

    
_success_response_schema_cache = {}

def make_success_schema_response(message, data_serializer=None, many=False, paginated=False):
    data_name = getattr(data_serializer, '__name__', 'Generic')
    slug = slugify(message)
    key_name = f"{data_name}_{slug}"
    digest = hashlib.md5(key_name.encode()).hexdigest()[:10]
    key = (data_name, many, paginated)
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
