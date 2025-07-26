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
        Final validation.
        """
        pwd = attrs['password']
        cpwd = attrs['confirm_password']
        if pwd != cpwd:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        
        # Validate profile data
        self._profile_data = {
            'first_name': attrs.get('first_name'),
            'last_name': attrs.get('last_name'),
            'telephone': attrs.get('telephone', '')
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
