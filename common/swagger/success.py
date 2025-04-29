from rest_framework import serializers
from .base import BaseResponseSerializer


# SUCCESS SERIALIZER FOR SWAGGER UI
class BaseSuccessSerializer(BaseResponseSerializer):
    """
    Base class for success serializers.
    """
    status = serializers.CharField(default='success')
    code = serializers.IntegerField(default=200)


class AcceptedSuccessSerializer(BaseSuccessSerializer):
    """
    Serializer for accepted success responses.
    """
    code = serializers.IntegerField(default=202)