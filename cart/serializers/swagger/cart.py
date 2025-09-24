from drf_spectacular.utils import OpenApiParameter, OpenApiTypes
from rest_framework import serializers

from common.swagger import (
    get_error_response,
    get_error_response_with_examples,
    get_success_response,
)
from cart.serializers.cart import CartSerializer
from product.api.v1.serializers import ProductSerializer

# SWAGGER SCHEMAS FOR CART

class AddToCartRequest(serializers.Serializer):
    """
    Serializer for the request data to add an item to the cart.
    """
    product = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(required=True, min_value=1, help_text="The quantity of the product to add to the cart.")

class UpdateCartItemRequest(serializers.Serializer):
    """
    Serializer for the request to update the quantity of an item in a cart.
    """
    operation = serializers.CharField(default='increment')

class CartValidationItemSerializer(serializers.Serializer):
    """
    Serializers for the items contained in the Cart Validation Response.
    """
    id = serializers.UUIDField()
    quantity = serializers.IntegerField(default=20, help_text='Quantity ordered by user.')
    stock = serializers.IntegerField(default=50, help_text='Available stock.')
    status = serializers.ChoiceField(choices=[
        'available', 'out_of_stock', 'insufficient_stock'])
    issue = serializers.ChoiceField(choices=[
        'Out of stock', 'Only 20 left in stock', None])
    product = ProductSerializer(exclude=['categories', 'stock'])


class CartValidationSerializer(serializers.Serializer):
    valid = serializers.BooleanField(default=True)
    items = CartValidationItemSerializer(many=True)

class GetCartResponse(serializers.Serializer):
    """
    Serializer for the response data when retrieving the cart.
    """
    status = serializers.CharField(default='success')
    message = serializers.CharField(default='Cart retrieved successfully.')
    data = CartValidationSerializer()


# add to cart schema
add_to_cart_404_examples = {
    'Missing product': 'Product not found',
    'Missing Cart': 'Cart not found'
}
add_to_cart_400_examples = {
    'Invalid quantity': 'Provide a valid quantity that is greater than 0.',
    'Invalid product id': 'Invalid product id.'
}

add_to_cart_schema = {
    'summary': 'Add item to cart',
    'description': 'Adds an item to the cart. Requires product_id and quantity in the request body.',
    'operation_id': 'add_to_cart',
    'tags': ['Cart'],
    'request': AddToCartRequest,
    'responses': {
        200: get_success_response('Item added to cart successfully.'),
        400: get_error_response_with_examples(examples=add_to_cart_400_examples),
        401: get_error_response_with_examples(code=401),
        404: get_error_response_with_examples(examples=add_to_cart_404_examples, code=404)
    }
}


# get cart schema
get_cart_schema = {
    'summary': 'Get cart',
    'description': 'Retrieves the current user\'s cart and all items in it.',
    'operation_id': 'get_cart',
    'tags': ['Cart'],
    'request': None,
    'responses': {
        200: GetCartResponse(),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Cart not found.', 404)
    }
}

# update cart schema
update_cart_error_examples = {
    'Cart item not found': 'Item not found in cart.',
    'Invalid operation': 'Invalid operation.',
    'Out of stock': 'Product out of stock.',
    'Zero quantity': 'Cannot remove from item with zero quantity.'
}

update_cart_schema = {
    'summary': 'Update cart items quantity',
    'description': 'Updates the quantity of an item in the cart. Requires product_id \
        as part of the path and quantity in the request body. If no quantity is provided, it defaults to 1.',
    'operation_id': 'update_cart',
    'tags': ['Cart'],
    'request': UpdateCartItemRequest,
    'responses': {
        200: get_success_response('Cart updated successfully.', 200, CartSerializer(many=True)),
        400: get_error_response_with_examples(update_cart_error_examples),
        401: get_error_response_with_examples(code=401),
        404: get_error_response('Product not found.', 404)
    }
}