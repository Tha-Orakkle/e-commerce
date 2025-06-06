from rest_framework import serializers

from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    BasePaginatedResponse,
    ForbiddenSerializer
)
from product.serializers.category import CategorySerializer

# SWAGGER SCHEMAS FOR CATEGORY
class CategoryDataRequest(serializers.Serializer):
    """
    Serializer for the request data to create or update a category.
    """
    name = serializers.CharField(required=True, max_length=120)

class CategoryDataError(serializers.Serializer):
    """
    Serializer for the error response when creating or updating a category.
    """
    name = serializers.ListField(child=serializers.CharField(), required=False)

class CategoryListResponse(BasePaginatedResponse):
    """
    Serializer for the response of a list of categories.
    """
    results = CategorySerializer(many=True)

# schamas
get_categories_schema = {
    'summary': 'Get all categories',
    'description': 'Returns a paginated list of all product categories.',
    'tags': ['Category'],
    'operation_id': 'get_categories',
    'request': None,
    'responses': {
        200: get_success_response("Categories retrieved successfully.", 200, CategoryListResponse()),
        401: get_error_response_with_examples(code=401)
    }
}

get_category_schema = {
    'summary': 'Get a specific category',
    'description': 'Takes a category id as part of url string and returns the details of the category.',
    'tags': ['Category'],
    'operation_id': 'get_category',
    'request': None,
    'responses': {
        200: get_success_response("Category retrieved successfully.", 200, CategorySerializer()),
        400: get_error_response("Invalid category id.", 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Category not found.", 404)
    }
}

create_category_schema = {
    'summary': 'Create a new category',
    'description': 'Accepts category data and returns the created category.',
    'tags': ['Category'],
    'operation_id': 'create_category',
    'request': CategoryDataRequest,
    'responses': {
        201: get_success_response("Category created successfully.", 201, CategorySerializer()),
        400: get_error_response("Category creation failed.", 400, CategoryDataError()),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer
    }
}

update_category_schema = {
    'summary': 'Update a specific category',
    'description': 'Updates a specific category by id.',
    'tags': ['Category'],
    'operation_id': 'update_category',
    'request': CategoryDataRequest,
    'responses': {
        200: get_success_response("Category updated successfully.", 200, CategorySerializer()),
        400: get_error_response("Category update failed.", 400, CategoryDataError()),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Category not found.", 404)
    }
}

delete_category_schema = {
    'summary': 'Delete a specific category',
    'description': 'Deletes a specific category by id.',
    'tags': ['Category'],
    'operation_id': 'delete_category',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response("Invalid category id.", 400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Category not found.", 404)
    }
}
