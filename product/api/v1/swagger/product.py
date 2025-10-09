from drf_spectacular.utils import OpenApiResponse
from decimal import Decimal
from rest_framework import serializers

from common.swagger import (
    build_invalid_id_error,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field,
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response,
    polymorphic_response
)


from product.api.v1.serializers import ProductSerializer


# PRODUCT SCHEMAS

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

class ProductCategoryRequestData(serializers.Serializer):
    """
    Serializer for the request data to add or remove categories from a product.
    """
    action = serializers.CharField(default="add")
    categories = serializers.ListField(child=serializers.CharField(default="category"))

    
# ERRORS 
invalid_shop_id_err = build_invalid_id_error('shop')

invalid_product_id_err = build_invalid_id_error('product')

shop_product_errors = {
    'validation_error': {
        'name': [
            'This field is required.',
            'This field may not be blank.',
            'Ensure this field has no more than 50 characters.'
        ],
        'description': [
            'This field is required.',
            'This field may not be blank.'
        ],
        'price': ['This field may not be blank.']
    }
}

product_category_error = {
    **invalid_product_id_err,
    'invalid_action': 'Enter a valid action: \'add\' or \'remove\'.',
    'missing_field': 'Please provide a list of categories in the \'categories\' field.',
    'missing_categories': 'Category with slug(s): \'<slug>\' not found.'
}


# SCHEMAS
get_shop_products_schema = {
    'summary': 'Get all shop products',
    'description': 'Returns a paginated list of products from a \
        specific shop.',
    'tags': ['Product'],
    'operation_id': 'get_shop_products',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Shop products retrieved successfully.",
            ProductSerializer,
            many=True,
            paginated=True
        ),
        400: make_error_schema_response(errors=invalid_shop_id_err),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['shop'])
    }
}

create_shop_product_schema = {
    'summary': 'Create a new product',
    'description': 'Accepts product data and return a created product. \
        Accessible to only staff.',
    'tags': ['Product'],
    'operation_id': 'create_product',
    'request': ProductDataRequest,
    'responses': {
        201: make_success_schema_response(
            "Product created successfully.",
            ProductSerializer
        ),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=invalid_shop_id_err),
                *build_error_schema_examples_with_errors_field(
                    message="Product creation failed.",
                    errors=shop_product_errors
                )
            ]
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['shop'])
    }
}

get_products_schema = {
    'summary': 'Get all products',
    'description': 'Returns a paginated list of products.',
    'tags': ['Product'],
    'operation_id': 'get_products',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Products retrieved successfully.",
            ProductSerializer,
            many=True,
            paginated=True    
        ),
        401: make_unauthorized_error_schema_response(),
    }
}

get_product_schema = {
    'summary': 'Get a specific product',
    'description': 'Returns a specific product by id passed to URL.',
    'tags': ['Product'],
    'operation_id': 'get_product',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Product retrieved successfully.",
            ProductSerializer    
        ),
        400: make_error_schema_response(errors=invalid_product_id_err),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['product'])
    }
}

update_product_schema = {
    'summary': 'Update a specific product',
    'description': 'Updates a specific product by id.',
    'tags': ['Product'],
    'operation_id': 'update_product',
    'request': ProductDataRequest,
    'responses': {
        200: make_success_schema_response(
            "Product updated successfully.",
            ProductSerializer
        ),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=invalid_product_id_err),
                *build_error_schema_examples_with_errors_field(
                    message="Product update failed.",
                    errors=shop_product_errors
                )
            ]
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product'])
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
        400: make_error_schema_response(errors=invalid_product_id_err),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product'])
    }
}

# category schema
product_category_add_or_remove_schema = {
    'summary': 'Add or remove category from a product',
    'description': 'Collects a list of categories and adds or removes them \
        from a product.Maximum number of categories for a product is 5.',
    'tags': ['ProductCategory'],
    'operation_id': 'add_or_remove_product_category',
    'request': ProductCategoryRequestData,
    'responses': {
        200: make_success_schema_response("Product categories updated successfully."),
        400: make_error_schema_response(errors=product_category_error),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product'])
    }
}
