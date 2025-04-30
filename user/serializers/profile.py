from rest_framework import serializers
from phonenumbers import parse, is_valid_number, NumberParseException
from user.models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'telephone', 'updated_at']


    def validate_first_name(self, value):
        """
        Validate the first name.
        """
        if len(value) < 2:
            raise serializers.ValidationError("Ensure this field has at least 2 characters.")
        return value.title().strip()

    def validate_last_name(self, value):
        """
        Validate the last name.
        """
        if len(value) < 2:
            raise serializers.ValidationError("Ensure this field has at least 2 characters.")
        return value.title().strip()
   
