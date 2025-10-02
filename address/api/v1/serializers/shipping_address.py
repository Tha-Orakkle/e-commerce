from rest_framework import serializers
from postal_codes_tools.postal_codes import verify_postal_code_format
from phonenumber_field.serializerfields import PhoneNumberField

from address.models import Country, City, State, ShippingAddress
from user.api.v1.serializers import UserSerializer
from common.exceptions import ErrorException

class ShippingAddressSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source='city.name', read_only=True)
    state = serializers.CharField(source='city.state.name', read_only=True)
    country = serializers.CharField(source='city.state.country.name', read_only=True)
    
    class Meta:
        model = ShippingAddress
        fields = ['id', 'full_name', 'telephone', 'street_address', 'city', 'state', 'country', 'postal_code']
        
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        
        if request and request.user.is_superuser:
            rep['user'] = UserSerializer(instance.user).data
        return rep


class ShippingAddressCreateUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(min_length=3, max_length=32)
    telephone = PhoneNumberField(region='NG')
    street_address = serializers.CharField(max_length=256)
    city = serializers.UUIDField()
    state = serializers.UUIDField()
    country = serializers.CharField(max_length=2)
    postal_code = serializers.CharField(max_length=20)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if not request:
            raise AssertionError("ShippingAddressCreateUpdateSerializer requires `request` in the context.")
        
        self._user = request.user

    def validate_full_name(self, value):
        return value.strip().title()
    
    def validate_telephone(self, value):
        try:
            return value.as_e164
        except AttributeError:
            raise serializers.ValidationError("Enter a valid phone number.")


    def _validate_postal_code(self, code, country_code):
        if not code:
            return code
        try:
            valid = verify_postal_code_format(country_iso2=country_code, postal_code=code)
        except KeyError:
            raise serializers.ValidationError(
                {'postal_code': 'Cannot validate postal code for the given country code.'}
            )
        if not valid:
            raise serializers.ValidationError(
                {'postal_code':'Invalid postal code format for the given country.'}
            )
        return code

    def _get_city_or_raise(self, city_id, state_id, country_code):
        city =  City.objects.select_related('state__country').filter(
            id=city_id, state_id=state_id, state__country__code=country_code).first()
        
        if city:
            return city
        
        if not Country.objects.filter(code=country_code).exists():
            raise serializers.ValidationError(
                {'country': f'Country with code not found or supported.'}
            )
            
        state = State.objects.select_related('country').filter(id=state_id).first()
        if not state:
            raise serializers.ValidationError({'state': 'State with given ID not found or supported.'})
        
        if state and state.country.code != country_code:
            raise serializers.ValidationError({'state': f'State does not belong to country with code.'})
        
        city = City.objects.filter(id=city_id).first()
        if not city:
            raise serializers.ValidationError({'city': 'City with given ID not found or supported.'})
        if city.state_id != state_id:
            raise serializers.ValidationError({'city': f'City does not belong to state.'})

        return city 
        
        
    def validate(self, attrs):
        if not self.instance:
            c_id = attrs.pop('city', '')
            s_id = attrs.pop('state', '')
            c_code = attrs.pop('country', '')
        elif self.instance:
            city = self.instance.city
            c_id = attrs.pop('city', city.id)
            s_id = attrs.pop('state', city.state_id)
            c_code = attrs.pop('country', city.state.country.code)
            
        city = self._get_city_or_raise(c_id, s_id, c_code)
        self._validate_postal_code(attrs.get('postal_code', None), c_code)
        attrs['city'] = city    
        return attrs
    
    
    def create(self, validated_data):
        if self._user.addresses.count() >= 5:
            raise ErrorException(
                detail="Customers can only have a maximum of 5 shipping addresses.",
                code='max_addresses_reached')
        return ShippingAddress.objects.create(
            user=self._user, **validated_data)
        
    def update(self, instance, validated_data):
        if not validated_data:
            return instance
    
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance