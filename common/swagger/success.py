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
