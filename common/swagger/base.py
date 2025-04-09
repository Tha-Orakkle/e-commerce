from rest_framework import serializers


# SWAGGER UI RESPONSE SERIALIZERS
class BaseResponseSerializer(serializers.Serializer):
    """
    Base class for Swagger serializers.
    """
    status = serializers.CharField()
    code = serializers.IntegerField()
    message = serializers.CharField()
