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
        read_only_fields = ['id', 'code']
        
    def __init__(self, *args, **kwargs):
        """
        Initialize the ShopSerializer.
        Remove field in the exclude arg.
        """
        exclude = kwargs.pop('exclude', None)
        super().__init__(*args, **kwargs)
        
        request = self.context.get('request', None)
        self._owner = request.user if request else None
        
        if exclude is not None:
            for field in exclude:
                self.fields.pop(field)

    def validate_name(self, value):
        """
        Validate the shop name.
        """
        value = value.strip()
        if not value:
            raise ValidationError("This field may not be blank.")
        if len(value) < 3:
            raise ValidationError("Shop name must be at least 3 characters.")
        if len(value) > 40:
            raise ValidationError("Shop name must not be more than 40 characters.")
        exists = Shop.objects.filter(name=value).first()
        should_raise = (
           (exists and not self._owner)
           or (exists and self._owner and self._owner.owned_shop.name != value) 
        )
        if should_raise:
            raise ValidationError("Shop with name already exists.")
        return value
    
    def validate_description(self, value):
        """
        Validate the shop description.
        """
        if value and len(value) < 10:        
            raise ValidationError("Shop description must be at least 10 characters.")
        if value and len(value) > 2000:
            raise ValidationError("Shop description must not be more than 2000 characters.")
        return value
