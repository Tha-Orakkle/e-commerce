from drf_spectacular.utils import OpenApiResponse

from common.swagger import (
    polymorphic_response,
    build_invalid_id_error,
    make_error_schema_response,
    make_not_found_error_schema_response,
    ForbiddenSerializer,
    make_success_schema_response,
    make_unauthorized_error_schema_response,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field
)

from shop.api.v1.serializers import ShopSerializer


shop_list_schema = {
    'summary': 'Get All Shops (Paginated)',
    'description': 'Retrieve a paginated list of all shops.',
    'tags': ['Shop'],
    'operation_id': 'get_shops',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shops retrieved successfully.",
            ShopSerializer,
            many=True,
            paginated=True
        ),
        401: make_unauthorized_error_schema_response(),
    }
}

errors = {**build_invalid_id_error('shop')}
patch_shop_errors = {
    'validation_error': {
        'name': [
            'This field may not be blank',
            'Ensure this field has at least 3 characters',
            'Ensure this field has no more than 40 characters.'
        ],
        'description': [
            'Ensure this field has at least 10 characters',
            'Ensure this field has no more than 2000 characters.'
        ]
    }
}


get_shop_schema = {
    'summary': 'Get a Specific Shop',
    'description': 'Retrieve a specific shop by its ID.',
    'tags': ['Shop'],
    'operation_id': 'get_shop',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shop retrieved successfully.",
            ShopSerializer
        ),
        400: make_error_schema_response(errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop']),
    }
}

patch_shop_schema = {
    'summary': 'Update a Specific Shop',
    'description': 'Update a specific shop by its ID. Only the shop owner can update their shop.',
    'tags': ['Shop'],
    'operation_id': 'update_shop',
    'request': ShopSerializer,
    'responses': {
        200: make_success_schema_response(
            "Shop updated successfully.",
            ShopSerializer
        ),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors),
                *build_error_schema_examples_with_errors_field(
                    message="Shop update failed.",
                    errors=patch_shop_errors
                )
            ]
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop']),
    }
}

delete_shop_schema = {
    'summary': 'Delete a Specific Shop',
    'description': 'Delete a specific shop by its ID and owner. Only the shop owner can delete their shop. \
        If the owner is also a customer, only associated shop is deleted and  and the user\'s \
        shop owner status is revoked else the user and shop are both deleted.',
    'tags': ['Shop'],
    'operation_id': 'delete_shop',
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors, 'invalid_uuid'),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop'])
    }
}
