from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_success_response,
    UnauthorizedSerializer
)    
from user.serializers.profile import UserProfileSerializer


# SWAGGER SCHEMAS FOR USER PROFILES
class ProfileDataRequest(serializers.Serializer):
    """
    Serializer for user profile requests.
    """
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    telephone = PhoneNumberField()


class ProfileDataError(serializers.Serializer):
    """
    Serializer for the error response when updating a user profile.
    """
    first_name = serializers.ListField(child=serializers.CharField(), required=False)
    last_name = serializers.ListField(child=serializers.CharField(), required=False)
    telephone = serializers.ListField(child=serializers.CharField(), required=False)


# schemas
update_user_profile_schema = {
    'summary': 'Update a user profile',
    'description': 'Accepts data to update the users profile. \
        Users can only update their profile',
    'tags': ['User'],
    'operation_id': 'update_user_profile',
    'request': ProfileDataRequest,
    'responses': {
        200: get_success_response('User profile updated successfully.', 200, UserProfileSerializer()),
        400: get_error_response('User profile update failed.', 400, ProfileDataError()),
        401: UnauthorizedSerializer
    }
}
