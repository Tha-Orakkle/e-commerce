from rest_framework import serializers

from address.models import State


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']
        read_only_fields = ['id']