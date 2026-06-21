from collections import defaultdict
from decimal import Decimal
from django.db import transaction
from django.db.models import F


from cart.utils.validators import validate_cart
from order.models import OrderGroup, Order, OrderItem
from order.domain.exceptions import EmptyCartError, InvalidCartError
from order.utils.delivery import calculate_delivery_fee
from product.models import Inventory



class CheckoutService:
    """
    Service to handle checking. Creates the order group, the orders for each shop
    and the items generally.
    """
    
    def __init__(self, user, cart, cart_items, shipping_address, payment_method, fulfillment_method):
        self.user = user
        self.cart = cart
        self.cart_items = cart_items
        self.shipping_address = shipping_address
        self.payment_method = payment_method
        self.fulfillment_method = fulfillment_method
        
        self.inventory_map = {}
        self.inventory_to_update = set()
        self.order_group = None
        self.orders_by_shop = {}
        self.group_total = Decimal()
        self.order_items = []
    
    
    def _validate_cart_not_empty(self):
        """
        Check that cart if not empty.
        """
        if not self.cart_items:
            raise EmptyCartError()        
    
    def _lock_inventory(self):
        """
        Lock all rows from the inventory table needed for the transaction.
        """
        inv_ids = {
            item.product.inventory.id
            for item in self.cart_items
        }
        
        inventories = Inventory.objects.select_for_update().filter(id__in=inv_ids)
        self.inventory_map = {inv.id: inv for inv in inventories}
        
    def _validate_and_prepare(self):
        """
        Validate cart items with the locked inventory data.
        validate that the products are still valid and available and 
        the stock is sufficient.
        """
        validated = validate_cart(self.cart_items)
        
        if not validated["is_valid"]:
            raise InvalidCartError(
                errors=[item for item in validated["items"]
                        if item["status"] != "available"])

    def _create_order_group(self):
        """
        Create the order group.
        """
        self.order_group = OrderGroup.objects.create(
            user=self.user,
            payment_method=self.payment_method, 
            shipping_address=self.shipping_address,
            fulfillment_method=self.fulfillment_method
        )
        
        if self.fulfillment_method == "DELIVERY":
            fee = Decimal(calculate_delivery_fee())
            self.order_group.delivery_fee = fee
            self.order_group.total_amount += fee
            

    def _create_orders_and_items(self):
        """
        Create the orders for each vendor and the order items.
        """
        for item in self.cart_items:
            product = item.product
            shop = product.shop
            qty = item.quantity
            price = product.price
            
            inv = self.inventory_map[product.inventory.id]

            # deduct stock from db using F
            inv._stock -= qty
            self.inventory_to_update.add(inv)
            
            # create order for each shop
            shop_id = shop.id
            
            if shop_id not in self.orders_by_shop:
                self.orders_by_shop[shop_id] = Order(
                    group=self.order_group,
                    shop=shop,
                    shop_name=shop.name
                )
                
            order = self.orders_by_shop[shop_id]

            line_total = qty * price
            order.total_amount += line_total
            self.group_total += line_total
            
            self.order_items.append(OrderItem(
                order=order,
                product=product,
                product_name=product.name,
                product_description=product.description,
                quantity=qty,
                price=price
            ))
            
    def _finalise(self):
        """
        Hit DB with the new orders and items.
        """
        orders = Order.objects.bulk_create(list(self.orders_by_shop.values()))
        order_map = {
            order.shop_id: order
            for order in orders
        }
        
        for item in self.order_items:
            item.order  = order_map[item.order.shop_id]
            
        OrderItem.objects.bulk_create(self.order_items)
        Inventory.objects.bulk_update(self.inventory_to_update, fields=["_stock"])
        
        self.order_group.total_amount += self.group_total
        self.order_group.save(update_fields=["total_amount", "delivery_fee"])
        
        
        self.cart_items.delete()

    def execute(self):
        """
        Implement checkout in an atomic transaction to handle race conditions.
        """
        self._validate_cart_not_empty()
        
        with transaction.atomic():
            self._lock_inventory()
            self._validate_and_prepare()
            self._create_order_group()
            self._create_orders_and_items()
            self._finalise()
            
        return self.order_group