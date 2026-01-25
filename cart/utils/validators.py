from rest_framework import status

from common.exceptions import ErrorException

from product.api.v1.serializers import ProductSerializer


def validate_cart(cart, include_shop=False):
    """
    Validates that the cart conatins available items.
    Args:
        cart (Cart): The cart to validate.
    Return:
        items (CartItem(many=True)): To prevent being called again by the caller function
        response (Dict): contains a `is_valid` key (boolean value) and `items` key (associated issues as value)
        response shape: {
            is_valid: True,
            items: [{
                id: item id,
                quantity: qty ordered,
                stock: qty left in stock,
                status: status of the product (available, unavailable,
                        out_of_stock, insufficient_stock),
                issue: Issues depending on status of the product,
                product: ProductSerializer()
            }]
        }
    """
    response = {
        'is_valid': True,
        'items': []
    }
    if not cart:
        raise ErrorException(
            detail="No cart for the user.",
            code='not_found',
            status_code=status.HTTP_404_NOT_FOUND)
    if not cart.items.exists():
        return [[], response]
    
    select = ['product__inventory']
    if include_shop:
        select.append('product__shop')

    cart_items = cart.items.select_related(*select)
    for item in cart_items:
        _item = {
            'id': item.id,
            'quantity': item.quantity,
            'stock': 0,
            'status': 'unavailable',
            'issue': "Product no longer available",
            'product': None
        }
        if item.product and item.product.is_active:
            _item['stock'] = item.product.stock
            _item['status'] = 'available'
            _item['issue'] = None
            _item['product'] = ProductSerializer(
                item.product, exclude=['categories', 'stock']).data
                
            if item.product.stock == 0:
                _item['status'] = 'out_of_stock'
                _item['issue'] = "Product out of stock"
                response['is_valid'] = False
            elif item.quantity > item.product.stock:
                _item['status'] = 'insufficient_stock'
                _item['issue'] = f"Only {item.product.stock} left in stock"
                response['is_valid'] = False
        else:
            response['is_valid'] = False
        response['items'].append(_item)
    return [cart_items, response]
