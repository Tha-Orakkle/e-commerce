from rest_framework import serializers

from product.serializers.product_image import ProductImageSerializer
from common.swagger import (
    get_success_response,
    get_error_response,
    get_error_response_with_examples,
    ForbiddenSerializer,
)


# SWAGGER SCHEMAS FOR PRODUCT IMAGE
class ProductImageDataRequest(serializers.Serializer):
    """
    Serializer for the request data to create a product image.
    """
    images = serializers.ListField(child=serializers.ImageField())


# schemas
get_product_images_schema = {
    'summary': 'Get all images of a product',
    'description': 'Takes a product id as part of url string \
        and returns the urls to product images.',
    'tags': ['Product-Image'],
    'operation_id': 'get_product_images',
    'request': None,
    'responses': {
        200: get_success_response("Product <product.name> images retrieved.", 200, ProductImageSerializer(many=True)),
        400: get_error_response("Invalid product id.", 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Product not found.", 404)
    }
}

get_product_image_schema = {
    'summary': 'Get a specific image of a product',
    'description': 'Takes a product id and image_id as part of url string \
        and returns the url to the product image.',
    'tags': ['Product-Image'],
    'operation_id': 'get_product_image',
    'request': None,
    'responses': {
        200: get_success_response("Product <product.name> image retrieved.", 200, ProductImageSerializer()),
        400: get_error_response("Invalid product image id.", 400),
        401: get_error_response_with_examples(code=401),
        404: get_error_response("Product image not found.", 404)
    }
}

create_product_image_schema = {
    'summary': 'Create new image(s) for a product',
    'description': 'Takes a product id as part of url string, \
        accepts an image data and returns a success message.',
    'tags': ['Product-Image'],
    'operation_id': 'create_product_image',
    'request': ProductImageDataRequest,
    'responses': {
        201: get_success_response("Product images added successfully.", 201),
        400: get_error_response("Invalid product id.", 400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Product not found.", 404)
    }   
}

delete_product_image_schema = {
    'summary': 'Create a new image for a product',
    'description': 'Takes a product_id and image_id as part of url string, \
        and deletes products images matching the image id.',
    'tags': ['Product-Image'],
    'operation_id': 'delete_product_image',
    'request': None,
    'responses': {
        204: {},
        400: get_error_response("Invalid product image id.", 400),
        401: get_error_response_with_examples(code=401),
        403: ForbiddenSerializer,
        404: get_error_response("Product image not found.", 404)
    }
}
