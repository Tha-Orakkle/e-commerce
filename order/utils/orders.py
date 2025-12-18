from decimal import Decimal
from django.db import transaction

from common.exceptions import ErrorException
from order.models import OrderGroup, Order, OrderItem
from order.utils.delivery import calculate_delivery_fee
from product.models import Inventory


def create_orders_from_cart(user, shipping_address, fulfillment_method, payment_method, cart_items):
    """
    Creates orders that be be group based on the shop the products belong to.
    All OrderItems belonging to the same shop will be in the same Order.
    Finally, all the orders will belong to an OrderGroup.    
    """
    
    with transaction.atomic():
        order_group = OrderGroup.objects.create(
            user=user,
            payment_method=payment_method,
            fulfillment_method=fulfillment_method,
            shipping_address=shipping_address
        )
        
        inv_ids = [ci.product.inventory.id for ci in cart_items]
        inventory_map = {
            inv.id: inv
            for inv in Inventory.objects.select_for_update()
            .filter(id__in=inv_ids)
        }
        group_total_amount = Decimal(calculate_delivery_fee()) if fulfillment_method == 'DELIVERY' else Decimal('0.00')
        order_by_shops = {}
        order_items_to_create = []
        
        for item in cart_items:
            product = item.product
            qty = item.quantity
            price = item.product.price
            inv = inventory_map[item.product.inventory.id]
            
            if qty > inv.stock:
                raise ErrorException(
                    detail=f"Insufficient stock for {item.product.name}. Only {inv.stock} left.",
                    code='insufficient_stock'
                )
                
                
            inv.subtract(qty=qty)
            
            shop_id = product.shop.id
            if shop_id not in order_by_shops:
                order = Order.objects.create(
                    group=order_group,
                    shop_id=shop_id
                )
                order_by_shops[shop_id] = order
            else:
                order = order_by_shops[shop_id]
            
            order.total_amount += qty * price
            group_total_amount += qty * price
            
            order_items_to_create.append(OrderItem(
                order=order,
                product=product,
                product_name=product.name,
                product_description=product.description,
                quantity=qty,
                price=price
            ))
        
        OrderItem.objects.bulk_create(order_items_to_create)
        Order.objects.bulk_update(order_by_shops.values(), ['total_amount'])
        order_group.total_amount = group_total_amount
        order_group.save(update_fields=['total_amount'])
        cart_items.delete()

    return order_group
        
        
        