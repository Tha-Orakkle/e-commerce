from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    BasePaginatedResponse,
    ForbiddenSerializer
)
from user.api.v1.serializers import UserSerializer

# SWAGGER SCHEMAS FOR ADMIN USERS
class ShopStaffListResponse(BasePaginatedResponse):
    """
    Serializer for paginated admin user list response.
    """
    results = UserSerializer(many=True)


class ShopStaffRequestData(serializers.Serializer):
    """
    Serializer for admin user registration requests.
    """
    staff_id = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()


class ShopStaffDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating an admin user.
    """
    staff_id = serializers.ListField(child=serializers.CharField(), required=False)
    password = serializers.ListField(child=serializers.CharField(), required=False)


# check if still necessary
get_shop_staff_schema = {
    'summary': 'Get all shop staff',
    'description': 'Returns a paginated list of shop staff. \
        Only superusers and shopowners can access this endpoint.',
    'operation_id': 'get_shop_staff',
    'tags': ['Shop-Staff'],
    'request': None,
    'responses': {
        200: get_success_response('Shop staff retrieved successfully.', 200, ShopStaffListResponse()),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("No shop found with the given code.", 404)
    }
}

shop_staff_member_404_errors = {
    'not_found': 'No staff memnber found with the given ID.',
    'not_found': 'No shop found with the given shop code.'
}

get_shop_staff_memeber_schema = {
    'summary': 'Get a specific shop staff member',
    'description': 'Takes the staff member id as part of the url \
        and returns matching staff member. \
        Only staff and superusers can access this endpoint. \
        As a staff member, you can not access other members data, only yours \
        except if you are the shop owner or a super user.',
    'operation_id': 'get_admin_user',
    'tags': ['Shop-Staff'],
    'request': None,
    'responses': {
        200: get_success_response('Shop staff member retrieved successfully.', 200, UserSerializer()),
        400: get_error_response('Invalid staff id.', 400),
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        # 404: get_error_response_with_examples(examples=shop_staff_member_404_errors, code)
        404: get_error_response('No staff memnber found with the given ID.', 404)
    }
}

update_shop_staff_memmber_schema = {
    'summary': 'Update a shop staff member',
    'description': 'Takes the shop staff id as part of the url. \
        Staff members can change only their passwords. \
        Shop owners can change data including staff handle \
        of any of their staff. Super users also have the permission.',
    'tags': ['Shop-Staff'],
    'operation_id': 'update_shop_staff_member',
    'request': ShopStaffRequestData,
    'responses': {
        200: get_success_response('Staff member updated successfully.', 200, UserSerializer()),
        400: get_error_response('Staff member update failed.', 400, ShopStaffDataError()),
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        404: get_error_response('No staff memnber found with the given ID.', 404)
    }
}

delete_shop_staff_member_schema = {
    'summary': 'Delete a shop staff member',
    'description': 'Takes a staff member\'s id as part of the url. \
        Only a shop owner can delete a staff member.',
    'tags': ['Shop-Staff'],
    'operation_id': 'delete_shop_staff',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response('Invalid staff id.', 400),
        401: get_error_response_with_examples(code=401), 
        403: ForbiddenSerializer,
        404: get_error_response('No staff memnber found with the given ID.', 404)
    }
}