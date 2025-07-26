from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from shop.models import Shop
from user.api.v1.serializers import UserSerializer


class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for the shop model.
    """
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Shop
        fields = '__all__'

    def validate_name(self, value):
        """
        Validate the shop name.
        """
        if not value:
            raise ValidationError("This field is required.")
        if len(value) < 3:
            raise ValidationError("Shop name must be at least 3 characters.")
        if len(value) > 40:
            raise ValidationError("Shop name must not be more than 40 characters.")
        if Shop.objects.filter(name=value).exists():
            raise ValidationError("Shop with name already exists.")
        return value
    
    def validate_description(self, value):
        """
        Validate the shop description.
        """
        if value and len(value) < 10:        
            raise ValidationError("Shop name must be at least 3 characters.")
        if value and len(value) > 2000:
            raise ValidationError("Shop name must not be more than 2000 characters.")
        return value
