from rest_framework import serializers

from common.swagger import (
    ForbiddenSerializer,
    make_unauthorized_error_schema_response,
    make_error_schema_response,
    make_success_schema_response,
    build_invalid_id_error
)
from cart.api.v1.serializers import CartSerializer, CartItemSerializer
from product.api.v1.serializers import ProductSerializer

# SWAGGER SCHEMAS FOR CART

class AddToCartRequest(serializers.Serializer):
    """
    Serializer for the request data to add an item to the cart.
    """
    product_id = serializers.UUIDField(required=True)
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


# CART SCHEMAS 
cart_error = {
    'Missing Cart': 'No cart found for the user.'
}
add_to_cart_errors_404 = {
    **cart_error,
    'Missing product': 'No product matching the given ID found.',
}
add_to_cart_errors_400 = {
    'invalid_quantity': 'Provide a valid quantity that is greater than 0.',
    **build_invalid_id_error('product')
}

add_to_cart_schema = {
    'summary': 'Add item to cart',
    'description': 'Adds an item to the cart. Requires product_id and quantity in the request body.',
    'operation_id': 'add_to_cart',
    'tags': ['Cart'],
    'request': AddToCartRequest,
    'responses': {
        200: make_success_schema_response(
            'Item added to cart successfully.', 
            CartSerializer),
        400: make_error_schema_response(errors=add_to_cart_errors_400),
        401: make_unauthorized_error_schema_response(),
        404: make_error_schema_response(errors=add_to_cart_errors_404, code='not_found')
    }
}

get_cart_schema = {
    'summary': 'Get cart',
    'description': 'Retrieves the current user\'s cart and all items in it. \
        Cart is validated and the response data contains the status and issue of each cart item.',
    'operation_id': 'get_cart',
    'tags': ['Cart'],
    'request': None,
    'responses': {
        200: GetCartResponse,
        401: make_unauthorized_error_schema_response(),
        404: make_error_schema_response(errors=cart_error)
    }
}

# CART ITEMS SCHEMA
cart_item_error_404 = {
    **cart_error,
    'Missing Cart Item': 'No item matching given ID found in cart.'
}
update_cart_item_errors = {
    'invalid_operation': 'Provide a valid operation: \'increment\' or \'decrement\'.',
    'insufficient_stock': 'Insufficient stock. Only <count> left.',
    'invalid_quantity': 'Cannot remove from item with zero quantity.',
    'produt_unavailable': 'Product no longer available.',
    **build_invalid_id_error('cart_itemm')
}

update_cart_item_schema = {
    'summary': 'Increment or decrement quantity of cart items by 1',
    'description': 'Increment/decrement the quantity of an items in the cart by 1. Requires cart item id \
        as part of the path.',
    'operation_id': 'update_cart',
    'tags': ['Cart'],
    'request': UpdateCartItemRequest,
    'responses': {
        200: make_success_schema_response(
            'Cart item updated successfully.',
            CartItemSerializer),
        400: make_error_schema_response(update_cart_item_errors),
        401: make_unauthorized_error_schema_response(),
        404: make_error_schema_response(errors=cart_item_error_404, code='not_found')
    }
}

get_cart_item_schema = {
    'summary': 'Get a cart item',
    'description': 'Get a cart item with the ID passed in the url path.',
    'operation_id': 'get_cart_item',
    'tags': ['Cart'],
    'request': None,
    'responses': {
        200: make_success_schema_response(
            'Cart item retrieved successfully.',
            CartItemSerializer
        ),
        400: make_error_schema_response(errors=build_invalid_id_error('cart item')),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_error_schema_response(errors=cart_item_error_404, code='not_found')
    }
}

delete_cart_item_schema =  {
    'summary': 'Delete a cart item',
    'description': 'Delete a cart item with the ID passed in the url path',
    'operation_id': 'delete_cart_item',
    'tags': ['Cart'],
    'request': None,
    'responses': {
        204: {},
        400: make_error_schema_response(errors=build_invalid_id_error('cart item')),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_error_schema_response(errors=cart_item_error_404, code='not_found')
    }
}
