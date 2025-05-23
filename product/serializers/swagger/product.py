from decimal import Decimal
from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    BasePaginatedResponse,
    ForbiddenSerializer,
    UnauthorizedSerializer
)
from product.serializers.product import ProductSerializer


# SWAGGER SCHEMAS FOR PRODUCT
class ProductListResponse(BasePaginatedResponse):
    """
    Serializer for paginated product list response.
    """
    results = ProductSerializer(many=True)


class ProductDataRequest(serializers.Serializer):
    """
    Serializer for the request data to create or update a product.
    """
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))
    images = serializers.ListField(
        child=serializers.ImageField(),
        required=False
    )


class ProductDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating a product.
    """
    name = serializers.ListField(child=serializers.CharField(), required=False)
    price = serializers.ListField(child=serializers.CharField(), required=False)
    

# schemas
create_product_schema = {
    'summary': 'Create a new product',
    'description': 'Accepts product data and return a created product.',
    'tags': ['Product'],
    'operation_id': 'create_product',
    'request': ProductDataRequest,
    'responses': {
        201: get_success_response('Product created successfully.', 201, ProductSerializer()),
        400: get_error_response('Product creation failed.', 400, ProductDataError()),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer
    }
}

get_products_schema = {
    'summary': 'Get all products',
    'description': 'Returns a paginated list of products.',
    'tags': ['Product'],
    'operation_id': 'get_products',
    'request': None,
    'responses': {
        200: get_success_response('Products retrieved successfully.', 200, ProductListResponse()),
        401: UnauthorizedSerializer,
    }
}

get_product_schema = {
    'summary': 'Get a specific products',
    'description': 'Returns a specific product by id.',
    'tags': ['Product'],
    'operation_id': 'get_product',
    'request': None,
    'responses': {
        200: get_success_response('Product retrieved successfully.', 200, ProductSerializer()),
        400: get_error_response('Invalid product id.', 400),
        401: UnauthorizedSerializer,
    }
}

update_product_schema = {
    'summary': 'Update a specific product',
    'description': 'Updates a specific product by id.',
    'tags': ['Product'],
    'operation_id': 'update_product',
    'request': ProductDataRequest,
    'responses': {
        200: get_success_response('Product updated successfully.', 200, ProductSerializer()),
        400: get_error_response('Product update failed.', 400, ProductDataError()),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer
    }
}

delete_product_schema = {
    'summary': 'Delete a specific product',
    'description': 'Deletes a specific product by id.',
    'tags': ['Product'],
    'operation_id': 'delete_product',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response('Invalid product id.', 400),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer
    }
}
