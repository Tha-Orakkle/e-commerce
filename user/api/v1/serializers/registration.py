from django.apps import apps
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth import get_user_model
from io import BytesIO
from PIL import Image
from rest_framework import serializers

import os
import uuid

from .base import BaseUserCreationSerializer
from .profile import UserProfileSerializer
from common.exceptions import ErrorException
from common.utils.bools import parse_bool
from cart.models import Cart

User = get_user_model()

LOGO_SIZE = (400, 400)

class ShopOwnerRegistrationSerializer(BaseUserCreationSerializer):
    email = serializers.EmailField()
    staff_handle = serializers.CharField(min_length=3, max_length=20)
    
    # shop fields
    shop_name = serializers.CharField(min_length=3, max_length=40)
    shop_description = serializers.CharField(
        min_length=10, max_length=2000, required=False, allow_blank=True)
    shop_logo = serializers.ImageField()
    already_customer = serializers.BooleanField(default=False)
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        """
        super().__init__(*args, **kwargs)
        self._existing_user = None
        self._profile_data = None
    
    
    def validate_staff_handle(self, value):
        """
        Convert staff handle to lowercase.
        """
        return value.strip().lower()
    
    def validate_email(self, value):
        """
        Validate the email address.
        """
        email = value.strip().lower()
        exists = User.objects.filter(email=email).first()
        if exists and not parse_bool(self.initial_data.get('already_customer', False)):
            raise serializers.ValidationError("User with email already exists.")
        if exists and exists.is_shopowner:
            raise serializers.ValidationError("Shop owner with email already exists.")
        self._existing_user = exists
        return email
    
    def validate_shop_name(self, value):
        """
        Validate the shop name.
        """
        Shop = apps.get_model('shop', 'Shop')
        value = value.strip()
        if Shop.objects.filter(name=value).exists():
            raise serializers.ValidationError("Shop with name already exists.")
        return value
    
    def validate_shop_logo(self, value):
        if not value:
            return None 
        img = Image.open(value)
        img.thumbnail(LOGO_SIZE, Image.LANCZOS)
        buffer = BytesIO()
        img_fmt = img.format if img.format else 'PNG'
        img.save(buffer, format=img_fmt)
        buffer.seek(0)
        ext = os.path.splitext(value.name)[1] or '.png'
        name = str(uuid.uuid4())[:8] + ext
        return InMemoryUploadedFile(
            file=buffer,
            field_name=getattr(img, 'field_name', None),
            name=name,
            content_type='image/jpeg',
            size=buffer.tell(),
            charset=getattr(img, 'charset', None)
        )

    
    def validate(self, attrs):
        """
        Retrieves the profile data.
        """
        self._profile_data = {
            'first_name': attrs.get('first_name'),
            'last_name': attrs.get('last_name'),
            'telephone': attrs.get('telephone')
        }
        return attrs

    def create(self, validated_data):
        already_customer = validated_data.pop('already_customer')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        
        shop_data = {
            'name': validated_data.pop('shop_name'),
            'description': validated_data.pop('shop_description', ''),
            'logo': validated_data.pop('shop_logo', None)
        }
        if already_customer and not self._existing_user:
            raise ErrorException(
                detail="Shop owner registration failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid credentials matching any customer.']}
            )
        if already_customer and self._existing_user:
            user = self._existing_user
            if not user.check_password(password):
                raise ErrorException(
                    detail="Shop owner registration failed.",
                    code="invalid_credentials",
                    errors={'non_field_errors': ['Invalid credentials matching any customer.']}
                )
            user.is_shopowner = True
            user.is_staff = True
            user.staff_handle = validated_data['staff_handle']
            user.save()
        else:
            user = User.objects.create_shopowner(
                email=validated_data['email'],
                staff_handle=validated_data['staff_handle'],
                password=password,
                already_customer=False               
            )
        
        # create/update the profile
        if self._existing_user:
            profile_serializer = UserProfileSerializer(
                instance=user.profile,
                data=self._profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        else:
            UserProfileSerializer().create({**self._profile_data, 'user': user})    
        
        # create the shop
        Shop = apps.get_model('shop', 'Shop')
        shop = Shop.objects.create(owner=user, **shop_data)
        return shop
    

class CustomerRegistrationSerializer(BaseUserCreationSerializer):
    email = serializers.EmailField()
    already_shopowner = serializers.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        """
        Initialize the serializer.
        """
        super().__init__(*args, **kwargs)
        self._existing_user = None
        self._profile_data = None
    
    def validate_email(self, value):
        """
        Validate the email address.
        """
        email = value.strip().lower()
        exists = User.objects.filter(email=email).first()
        if exists and not parse_bool(self.initial_data.get('already_shopowner', False)):
            raise serializers.ValidationError("User with email already exists.")
        if exists and exists.is_customer:
            raise serializers.ValidationError("Customer with email already exists.")
        self._existing_user = exists
        return email
    
    def validate(self, attrs):
        """
        Retrieves the profile data.
        """
        self._profile_data = {
            'first_name': attrs.get('first_name'),
            'last_name': attrs.get('last_name'),
            'telephone': attrs.get('telephone')
        }

        return attrs
    
    def create(self, validated_data):
        already_shopowner = validated_data.pop('already_shopowner')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')
        
        if already_shopowner and not self._existing_user:
            raise ErrorException(
                detail="Customer registration failed.",
                code="invalid_credentials",
                errors={'non_field_errors': ['Invalid credentials matching any shop owner.']}
            )
        if already_shopowner and self._existing_user:
            user = self._existing_user
            if not user.check_password(password):
                raise ErrorException(
                    detail="Customer registration failed.",
                    code="invalid_credentials",
                    errors={'non_field_errors': ['Invalid credentials matching any shop owner.']}
                )
            user.is_customer = True
            user.save()
        else:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=password
            )

        # create/update the profile
        if self._existing_user:
            profile_serializer = UserProfileSerializer(
                instance=user.profile,
                data=self._profile_data,
                partial=True
            )
            profile_serializer.is_valid(raise_exception=True)
            profile_serializer.save()
        else:
            UserProfileSerializer().create({**self._profile_data, 'user': user})    
        
        # create a cart for the customer
        Cart.objects.create(user=user)
        return user
