from drf_spectacular.utils import OpenApiResponse
from rest_framework import serializers


from common.swagger import (
    build_invalid_id_error,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field,
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response,
    polymorphic_response
)
from user.api.v1.serializers import UserSerializer



# SCHEMA FOR STAFF MEMBERS

class ShopStaffUpdateRequestData(serializers.Serializer):
    staff_handle = serializers.CharField()


get_shop_staff_members_schema = {
    'summary': 'Get all shop staff members',
    'description': 'Returns a paginated list of all staff members of the \
        shop matching the ID passed to the URL. Only superusers and \
        shopowners can access this endpoint. Shop owners can only get the \
        staff members associated with their shops.',
    'operation_id': 'get_shop_staff',
    'tags': ['Shop-Staff'],
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shop staff retrieved successfully.",
            UserSerializer,
            many=True,
            paginated=True),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop'])
    }
}

invalid_id_errors = {
    **build_invalid_id_error('shop'),
    **build_invalid_id_error('staff')
}

get_shop_staff_member_schema = {
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
        200: make_success_schema_response(
            "Shop staff member retrieved successfully.",
            UserSerializer),
        400: make_error_schema_response(errors=invalid_id_errors),
        401: make_unauthorized_error_schema_response(), 
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop', 'staff member'])
    }
}

patch_errors = {
    'validation_error': {
        'staff_handle': ['Staff member with staff handle already exists.']
    }
}

patch_shop_staff_member_schema = {
    'summary': 'Update a shop staff member',
    'description': 'Update the staff handle of a staff member of a shop. \
        The staff member ID and the shop ID will be passed to the URL.\
        Only accessible to super users and shop owners. Shop owners can update data \
        of staff associated with their shops.',
    'tags': ['Shop-Staff'],
    'operation_id': 'update_shop_staff_member',
    'request': ShopStaffUpdateRequestData,
    'responses': {
        200: make_success_schema_response(
            "Staff member updated successfully.",
            UserSerializer),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples_with_errors_field(
                    message="Staff member update failed.",
                    errors=patch_errors),
                *build_error_schema_examples(errors=invalid_id_errors)
            ]
        ),
        401: make_unauthorized_error_schema_response(), 
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop', 'staff member'])
    }
}

delete_shop_staff_member_schema = {
    'summary': 'Delete a shop staff member',
    'description': 'Delete a staff member of a shop. \
        The staff member ID and the shop ID will be passed to the URL.\
        Only accessible to super users and shop owners. Shop owners can update data \
        of staff associated with their shops.',
    'tags': ['Shop-Staff'],
    'operation_id': 'delete_shop_staff_member',
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors=invalid_id_errors),
        401: make_unauthorized_error_schema_response(), 
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop', 'staff member'])
    }
}