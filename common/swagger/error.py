from rest_framework import serializers

from .base import BaseResponseSerializer


# ERROR SERIALIZERS FOR SWAGGER UI
class BaseErrorSerializer(BaseResponseSerializer):
    """
    Base class for error serializers.
    """
    status = serializers.CharField(default='error')


class BadRequestSerializer(BaseErrorSerializer):
    """
    Serializer for bad request responses.
    """
    code = serializers.IntegerField(default=400)


class UnauthorizedSerializer(BaseErrorSerializer):
    """
    Serializer for unauthorized responses.
    """
    code = serializers.IntegerField(default=401)
    

class ForbiddenSerializer(BaseErrorSerializer):
    """
    Serializer for forbidden responses.
    """
    code = serializers.IntegerField(default=403)


class NotFoundSerializer(BaseErrorSerializer):
    """
    Serializer for not found responses.
    """
    code = serializers.IntegerField(default=404)