from rest_framework import serializers

from product.api.v1.serializers import ProductImageSerializer
from common.swagger import (
    build_invalid_id_error,
    ForbiddenSerializer,
    make_success_schema_response,
    make_error_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response
)


# SWAGGER SCHEMAS FOR PRODUCT IMAGE
class ProductImageDataRequest(serializers.Serializer):
    """
    Serializer for the request data to create a product image.
    """
    images = serializers.ListField(child=serializers.ImageField())


# schemas
invalid_id_error = build_invalid_id_error('product')
invalid_id_errors = {
    **invalid_id_error,
    **build_invalid_id_error('product image')
}


get_product_images_schema = {
    'summary': 'Get all images of a product',
    'description': 'Takes a product id as part of url \
        and returns the urls to product images.',
    'tags': ['Product-Image'],
    'operation_id': 'get_product_images',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Product images retrieved successfully.",
            ProductImageSerializer,
            many=True),
        400: make_error_schema_response(errors=invalid_id_error),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['product'])
    }
}


get_product_image_schema = {
    'summary': 'Get a specific image of a product',
    'description': 'Takes a product id and image_id as part of url \
        and return the url to the product image.',
    'tags': ['Product-Image'],
    'operation_id': 'get_product_image',
    'request': None,
    'responses': {
        200: make_success_schema_response(
            "Product image retrieved successfully.",
            ProductImageSerializer),
        400: make_error_schema_response(errors=invalid_id_errors),
        401: make_unauthorized_error_schema_response(),
        404: make_not_found_error_schema_response(['product', 'product image']),
    }
}

create_image_errors = {
    **invalid_id_error,
    'no_image': 'No image was provided.',
    'image_limit_exceeded': 'Product images cannot exceed 8. Cannot add more images.',
    
}

create_product_image_schema = {
    'summary': 'Create new image(s) for a product',
    'description': 'Takes a product id as part of url, \
        accepts an image data and returns a success message.',
    'tags': ['Product-Image'],
    'operation_id': 'create_product_image',
    'request': ProductImageDataRequest,
    'responses': {
        201: make_success_schema_response("Product images added successfully."),
        400: make_error_schema_response(errors=create_image_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product'])
    }
}

delete_product_image_schema = {
    'summary': 'Delete a product image',
    'description': 'Takes a product_id and image_id as part of url string, \
        and deletes products images matching the image id.',
    'tags': ['Product-Image'],
    'operation_id': 'delete_product_image',
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors=invalid_id_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product', 'product image']),
    }
}
