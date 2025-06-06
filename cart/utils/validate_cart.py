from rest_framework import status

from common.exceptions import ErrorException

from product.serializers.product import ProductSerializer


def validate_cart(cart):
    """
    Validates that the cart conatins available items.
    Args:
        cart (Cart): The cart to validate.
    """
    response = {
        'valid': True,
        'items': []
    }
    if not cart:
        raise ErrorException("Cart not found.", code=status.HTTP_404_NOT_FOUND)
    if not cart.items.exists():
        return response
    
    # gets all the products and inventory with SQL join
    cart_items = cart.items.select_related('product__inventory')
    for item in cart_items:
        _item = {
            'id': item.id,
            'quantity': item.quantity,
            'stock': item.product.inventory.stock,
            'status': 'available',
            'issue': None,
            'product': ProductSerializer(
                item.product, exclude=['categories', 'stock']).data
        }
        if item.product.inventory.stock == 0:
            _item['status'] = 'out_of_stock'
            _item['issue'] = "Out of stock"
            response['valid'] = False
        elif item.quantity > item.product.inventory.stock:
            _item['status'] = 'insufficient_stock'
            _item['issue'] = f"Only {item.product.inventory.stock} left in stock"
            response['valid'] = False
        response['items'].append(_item)
    return response
