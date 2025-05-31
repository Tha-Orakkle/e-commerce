from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_success_response,
    UnauthorizedSerializer,
    ForbiddenSerializer
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

class ProfileCategoryRequestData(serializers.Serializer):
    """
    Serializer for the request data to add or remove categories from a product.
    """
    action = serializers.CharField(default="add")
    categories = serializers.ListField(child=serializers.CharField(default="category"))



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


user_profile_category_add_or_remove_schema = {
    'summary': 'Update a user preferred categories',
    'description': 'Collects a list categories and adds or removes them from user\'s preferred categories.',
    'tags': ['User-Category'],
    'operation_id': 'user_preferred_categories',
    'request': ProfileCategoryRequestData,
    'responses': {
        200: get_success_response("Product categories updated successfully.", 200),
        400: get_error_response("Invalid action.", 400),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer,
        404: get_error_response("Product not found.", 404)
    }
}