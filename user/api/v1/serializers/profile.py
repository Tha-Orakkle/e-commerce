from rest_framework import serializers
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
   
    def update(self, instance, validated_data):
        """
        Updates a user profile.
        """
        try:
            categories = self.initial_data.getlist('categories', [])
            if categories:
                instance.add_categories(categories)
        except Exception:
            pass
        return super().update(instance, validated_data)