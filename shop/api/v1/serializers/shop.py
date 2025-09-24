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
        super().__init__(*args, **kwargs)        
        request = self.context.get('request', None)
        self._user = getattr(request, 'user', None)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        view = self.context.get('view')

        if self._user and self._user.is_superuser:
            return rep        
   
        from user.api.v1.routes import ShopOwnerRegistrationView
        if not isinstance(view, ShopOwnerRegistrationView):
            rep.pop('owner', None)
            rep.pop('code', None)

        if self._user and self._user.is_authenticated:
            if instance in (getattr(self._user, 'owned_shop', None), getattr(self._user, 'shop', None)):
                rep['code'] = instance.code
        return rep

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
        # raise error if shop with name exists and it is not the 
        # current user's shop.
        should_raise = (
           (exists and not self.user)
           or (exists and self.user and self.user.owned_shop.name != value) 
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
