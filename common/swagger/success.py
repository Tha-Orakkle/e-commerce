from rest_framework import serializers
from .base import BaseResponseSerializer


# SUCCESS SERIALIZER FOR SWAGGER UI
class BaseSuccessSerializer(BaseResponseSerializer):
    """
    Base class for success serializers.
    """
    code = serializers.IntegerField(default=200)
    status = serializers.CharField(default='success')