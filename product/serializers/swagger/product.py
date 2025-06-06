from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from decimal import Decimal
from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    BasePaginatedResponse,
    ForbiddenSerializer,
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


class ProductCategoryRequestData(serializers.Serializer):
    """
    Serializer for the request data to add or remove categories from a product.
    """
    action = serializers.CharField(default="add")
    categories = serializers.ListField(child=serializers.CharField(default="category"))

    

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
        401: get_error_response_with_examples(code=401),
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
        401: get_error_response_with_examples(code=401),
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
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Product not found.', 404)
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
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response('Product not found.', 404)
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
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response('Product not found.', 404)
    }
}

# add parameters 'action' to schema
product_category_error_examples = {
    'Invalid action': 'Invalid action.',
    'Invalid product id': 'Invalid product id.'
}

product_category_add_or_remove_schema = {
    'summary': 'Add or remove category from a product',
    'description': 'Collects a list of categories and adds or removes them from a product. Maximum number of categories for a product is 5.',
    'tags': ['Product-Category'],
    'operation_id': 'add_or_remove_product_category',
    'request': ProductCategoryRequestData,
    'parameters': [
        OpenApiParameter(
            name='action',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Action to perform: "add" or "remove". Default is "add".',
            required=True
        )

    ],
    'responses': {
        200: get_success_response("Product categories updated successfully.", 200),
        400: get_error_response_with_examples(examples=product_category_error_examples),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Product not found.", 404),

    }
}