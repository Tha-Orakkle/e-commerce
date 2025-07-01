from phonenumbers import parse, is_valid_number, NumberParseException
from postal_codes_tools.postal_codes import verify_postal_code_format
from rest_framework import serializers


from address.models import Country, ShippingAddress
from common.exceptions import ErrorException


def validate_location(country_code, state_id, city_id):
    """
    Validate the shipping address data.
    """
    errors = {}
    country = None
    state = None
    city = None
    
    if not country_code:
        errors['country'] = "Please provide the country code (ISO 2)."
    else:
        country = Country.objects.prefetch_related('states__cities').filter(code=country_code).first()
        if not country:
            errors['country'] = "Invalid or unsupported country code."
    
    if not errors.get('country') and state_id:
        state = next((s for s in country.states.all() if str(s.id) == state_id), None)
        if not state:
            errors['state'] = "Invalid or unsupported state."
    elif not state_id:
        errors['state'] = "Please provide a state id."

    if not errors.get('state') and city_id:
        city = next((c for c in state.cities.all() if str(c.id) == city_id), None)
        if not city:
            errors['city'] = "Invalid or unsupported city."
    elif not city_id:
        errors['city'] = "Please provide a city id."

    if errors:
        return errors, None
    
    return errors, city



class ShippingAddressSerializer(serializers.ModelSerializer):
    city = serializers.CharField(source='city.name', read_only=True)
    state = serializers.CharField(source='city.state.name', read_only=True)
    country = serializers.CharField(source='city.state.country.name', read_only=True)   

    class Meta:
        model = ShippingAddress
        fields = ['id', 'full_name', 'telephone', 'street_address', 'city', 'state', 'country', 'postal_code']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """
        Create a new ShippingAddress instance.
        """
        data = self.initial_data
        country_code = data.get('country')
        state_id = data.get('state')
        city_id = data.get('city')
        errors, city = validate_location(country_code, state_id, city_id)
        if errors:
            raise ErrorException(
                "Shipping address creation failed.",
                code=400,
                errors=errors
            )
        user = validated_data.get('user')
        if not user:
            raise ErrorException("User must be provided to create a shipping address.", code=400)
        if user.addresses.count() >= 5:
            raise ErrorException("You can only have a maximum of 5 shipping addresses.", code=400)
        return ShippingAddress.objects.create(city=city, **validated_data)

    def update(self, instance, validated_data):
        data = self.initial_data
        country_code = data.get('country')
        state_id = data.get('state')
        city_id = data.get('city')
        errors, city = validate_location(country_code, state_id, city_id)
        if errors:
            raise ErrorException(
                "Shipping address creation failed.",
                code=400,
                errors=errors
            )
        user = validated_data.get('user')
        if not user:
            raise ErrorException("User must be provided to create a shipping address.", code=400)
        
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.city = city
        instance.save()
        return instance
        
    def validate_full_name(self, value):
        """
        Validate the full name.
        """
        if len(value) < 2:
            raise serializers.ValidationError("Full name must be at least 2 characters long.")
        return value.title().strip()
    
    def validate_telephone(self, value):
        """
        Validate telephone number to ensure that is valid for the country entered.
        """
        country_code = self.initial_data.get('country')
        try:
            parsed_number = parse(value, country_code)
        except NumberParseException:
            raise serializers.ValidationError("Invalid telephone number.")
        if not is_valid_number(parsed_number):
            raise serializers.ValidationError("Telephone entered is not a valid number in the country you selected.")
        return value
    
    def validate_postal_code(self, value):
        """
        Validate the postal code for the country entered.
        """
        country_code = self.initial_data.get('country')
        if not value:
            raise serializers.ValidationError('Please provide the postal code.')
        is_valid = False
        try:
            is_valid = verify_postal_code_format(country_iso2=country_code, postal_code=value)
        except KeyError:
            raise serializers.ValidationError("Invalid country iso 2 code.")
        if not is_valid:
            raise serializers.ValidationError("Invalid postal code.")
        return value
