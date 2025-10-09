from drf_spectacular.utils import OpenApiResponse

from common.swagger import (
    build_invalid_id_error,
    build_error_schema_examples,
    build_error_schema_examples_with_errors_field,
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response,
    make_error_schema_response_with_errors_field,
    make_unauthorized_error_schema_response,
    make_not_found_error_schema_response,
    polymorphic_response,
)
from product.api.v1.serializers.category import CategorySerializer

# # SWAGGER SCHEMAS FOR CATEGORY
# class CategoryDataRequest(serializers.Serializer):
#     """
#     Serializer for the request data to create or update a category.
#     """
#     name = serializers.CharField(required=True, max_length=120)

# class CategoryDataError(serializers.Serializer):
#     """
#     Serializer for the error response when creating or updating a category.
#     """
#     name = serializers.ListField(child=serializers.CharField(), required=False)

# class CategoryListResponse(BasePaginatedResponse):
#     """
#     Serializer for the response of a list of categories.
#     """
#     results = CategorySerializer(many=True)

# CATEGORY SCHEMAS
# errors
invalid_id_error = build_invalid_id_error('category')

category_errors = {
    'validation_errors': {
        'name': [
            'This field is required.',
            'This field may not be blank.',
            'Ensure this field has at least 2 characters.',
            'Ensure this field has no more than 120 characters.'
        ]
    }
}

# schemas

get_categories_schema = {
    'summary': 'Get all categories',
    'description': 'Returns a paginated list of all product categories.',
    'tags': ['Category'],
    'operation_id': 'get_categories',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Categories retrieved successfully.",
            CategorySerializer,
            many=True, 
            paginated=True    
        ),
        401: make_unauthorized_error_schema_response()
    }
}

get_category_schema = {
    'summary': 'Get a specific category',
    'description': 'Takes a category id as part of url string and returns the details of the category.',
    'tags': ['Category'],
    'operation_id': 'get_category',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Category retrieved successfully.",
            CategorySerializer),
        400: make_error_schema_response(errors=invalid_id_error),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['category'])
    }
}

create_category_schema = {
    'summary': 'Create a new category',
    'description': 'Accepts category data and returns the created category. \
        Only accessible to super users.',
    'tags': ['Category'],
    'operation_id': 'create_category',
    'request': CategorySerializer,
    'responses': {
        201: make_success_schema_response(
            "Category created successfully.",
            CategorySerializer
        ),
        400: make_error_schema_response_with_errors_field(
            message="Category creation failed.",
            errors=category_errors    
        ),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer
    }
}

update_category_schema = {
    'summary': 'Update a specific category',
    'description': 'Updates a specific category by id. \
        Only accessible to super users.',
    'tags': ['Category'],
    'operation_id': 'update_category',
    'request': CategorySerializer,
    'responses': {
        200: make_success_schema_response(
            "Category updated successfully.",
            CategorySerializer
        ),
        400: OpenApiResponse(
            response=polymorphic_response,
            examples=[
                *build_error_schema_examples(errors=invalid_id_error),
                *build_error_schema_examples_with_errors_field(
                    errors=category_errors,
                    message="Category update failed."
                )
            ]
        ),  
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['category'])
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
        400: make_error_schema_response(errors=invalid_id_error),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['category'])
    }
}
