from rest_framework import serializers


class BasePaginatedResponse(serializers.Serializer):
    count = serializers.IntegerField(default=1)
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)