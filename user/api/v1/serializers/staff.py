from django.contrib.auth import get_user_model
from rest_framework import serializers

from .base import BaseUserCreationSerializer
from .profile import UserProfileSerializer

User = get_user_model()

class ShopStaffCreationSerializer(BaseUserCreationSerializer):
    staff_id = serializers.CharField(min_length=3, max_length=20)
   
    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        """
        super().__init__(*args, **kwargs)
        self._shop = self.context.get('shop')
        if not self._shop:
            raise serializers.ValidationError({'shop': ['Shop context is required.']}) 
        self._profile_data = None
        
    def validate_staff_id(self, value):
        """
        Validate the staff ID.
        """
        staff_id = value.strip().lower()
        if self._shop and self._shop.staff_id_exists(staff_id):
            raise serializers.ValidationError("Staff member with staff ID already exists.")
        return staff_id
    
    def validate(self, attrs):
        """
        Retrieve the profile data.
        """
        # Validate profile data
        self._profile_data = {
            'first_name': attrs.get('first_name').title(),
            'last_name': attrs.get('last_name').title(),
            'telephone': attrs.get('telephone', '').title()
        }
        return attrs
    
    def create(self, validated_data):
        """
        Create a new staff member.
        """
        staff = User.objects.create_staff(
            shop=self._shop,
            staff_id=validated_data['staff_id'],
            password=validated_data['password'],
        )
        # Create the profile
        UserProfileSerializer().create({**self._profile_data, 'user': staff})
        return staff


class StaffUpdateSerializer(serializers.Serializer):
    staff_id = serializers.CharField(
        required=True, min_length=3, max_length=20)

    def __init__(self, *args, **kwargs):
        """
        Initialize the staff update serializer.
        Get the shop obj and the staff to be updated. 
        """
        super().__init__(*args, **kwargs)
        self._shop = self.context.get('shop')
        self._staff = self.context.get('staff', None)
        
        if not self._shop:
            raise AssertionError(
                "UpdateStaffSerializer requires the shop in the context."
            )
        if not self._staff:
            raise AssertionError(
                "UpdateStaffSerializer requires a the target staff to be updated in the context."
            )

    def validate_staff_id(self, value):
        """
        Ensure the staff id passed does not already exist in the shop.
        """
        value = value.strip().lower()
        if self._shop.staff_id_exists(value) and self._staff.staff_id != value:
            raise serializers.ValidationError("Staff member with staff handle already exists.")
        return value
    
    def save(self, **kwargs):
        """
        Save changes.
        Ensure updates only occur when real changes are made.
        """
        new = self.validated_data['staff_id']
        if new != self._staff.staff_id:
            self._staff.staff_id = new
            self._staff.save(update_fields=['staff_id', 'updated_at'])
        return self._staff
