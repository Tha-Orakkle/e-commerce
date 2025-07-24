from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response,
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
        401: get_error_response_with_examples(code=401),
        404: get_error_response('User has no profile', 404)
    }
}

# add 'action' query parameter to the request
user_category_404_examples = {
    'Missing profile': 'User has no profile',
    'Missing product': 'Product not found'
}
user_profile_category_add_or_remove_schema = {
    'summary': 'Update a user preferred categories',
    'description': 'Collects a list categories and adds or removes them from user\'s preferred categories.',
    'tags': ['User-Category'],
    'operation_id': 'user_preferred_categories',
    'request': ProfileCategoryRequestData,
    'parameters': [OpenApiParameter(
        name='action',
        type=OpenApiTypes.STR,
        description="Could be 'add' or 'remove'",
        location=OpenApiParameter.QUERY,
        required=True
    )],
    'responses': {
        200: get_success_response("Product categories updated successfully.", 200),
        400: get_error_response("Invalid action.", 400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response_with_examples(user_category_404_examples)
    }
}