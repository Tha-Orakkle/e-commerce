from rest_framework import status

from product.api.v1.serializers import ProductSerializer


def validate_cart(cart_items, inventory_map=None):
    """
    Unified cart validator.

    Modes:
    - Pre-check: inventory_map=None → uses product.stock
    - Post-lock: inventory_map=locked inventories → uses DB truth
    """
    response = {
        "is_valid": True,
        "items": []
    }
    
    for item in cart_items:
        product = item.product
        qty = item.quantity

        _item = {
            "id": item.id,
            "quantity": qty,
            "stock": 0,
            "status": "unavailable",
            "issue":"Product no longer available",
            "product": None
        }
        
        # Determine product vailidity 
        if not product or not product.is_active:
            response["is_valid"] = False
            response["items"].append(_item)
            continue
        
        # Determine stock source
        if inventory_map is None:
            # PRE-CHECK MODE (UX only)
            stock = product.stock
        else:
            # POST-LOCK MODE (authoritative truth)
            inv = inventory_map.get(product.inventory_id)
            if not inv:
                _item["status"] = "inventory_missing"
                _item["issue"] = "Inventory missing"
                response["is_valid"] = False
                response["items"].append(_item)
                continue
             
            stock = inv._stock

        _item["stock"] = stock
        _item["product"] = ProductSerializer(
            product,
            exclude=["categories", "stock"]
        ).data
        
        # stock rules
        if stock == 0:
            _item["status"] = "out_of_stock"
            _item["issue"] = "Product out of stock"
            response["is_valid"] = False
        elif qty > stock:
            _item["status"] = "insufficient_stock"
            _item["issue"] = f"Only {stock} left in stock"
            response["is_valid"] = False
        else:
            _item["status"] = "available"
            _item["issue"] = None

        response["items"].append(_item)

    return response
