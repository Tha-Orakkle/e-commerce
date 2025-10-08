from rest_framework import serializers

from common.swagger import (
    ForbiddenSerializer,
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    make_error_schema_response,
    make_error_schema_response_with_errors_field,
)

from user.api.v1.serializers import UserProfileSerializer


class ProfileCategoryRequestData(serializers.Serializer):
    """
    Serializer for the request data to add or remove categories from a product.
    """
    action = serializers.CharField(default="add")
    categories = serializers.ListField(child=serializers.CharField(default="category"))


# UPDATE PROFILE DATA SCHEMA
no_profile_error = {
    'not_found': 'User has no profile.',
}

update_profile_erorrs = {
    'validation_error': {
        'first_name': [
            'This field may not be blank',
            'Ensure this field has at least 2 characters.',
            'Ensure this field has no more than 30 characters.'
        ],
        'last_name': [
            'This field may not be blank',
            'Ensure this field has at least 2 characters.',
            'Ensure this field has no more than 30 characters.'
        ],
        'telephone': ['Enter a valid phone number.']
    },
}


update_user_profile_schema = {
    'summary': 'Update a user profile',
    'description': ' Update a user\'s profile data. Target user is the authenticated user',
    'tags': ['User'],
    'operation_id': 'update_user_profile',
    'request': UserProfileSerializer,
    'responses': {
        200: make_success_schema_response(
            "User profile updated successfully.",
            UserProfileSerializer),
        400: make_error_schema_response_with_errors_field(
            message="user profile update failed.",
            errors=update_profile_erorrs
        ),
        401: make_unauthorized_error_schema_response(),
        404: make_error_schema_response(errors=no_profile_error)
    }
}


# UPDATE USER PREFERRED CATEGORY SCHEMA
category_errors = {
    'missing_categories': 'Please provide a list of categories in the \'categories\' field.',
    'invalid_action': 'Enter a valid action: \'add\' or \'remove\'.'
}

update_user_preferred_category_schema = {
    'summary': 'Update a user preferred categories',
    'description': 'Collects a list categories and adds or removes them from \
        user\'s preferred categories. Takes operation to be performed in the request body.',
    'tags': ['User-Category'],
    'operation_id': 'user_preferred_categories',
    'request': ProfileCategoryRequestData,
    'responses': {
        200: make_success_schema_response(
            "User preferred categories updated successfully."),
        400: make_error_schema_response(errors=category_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_error_schema_response(errors=no_profile_error)
    }
}
