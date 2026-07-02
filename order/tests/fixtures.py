from decimal import Decimal

import pytest

from order.models import OrderGroup, Order, OrderItem
from order.utils.delivery import calculate_delivery_fee


@pytest.fixture
def order_group_factory(customer_factory, shipping_address_factory):
    """
    Factory for creating order groups for a user.
    """
    def create_order_group(user=None, address=None, **kwargs):
        user = user or customer_factory()
        address = address or shipping_address_factory(user=user)

        order_group = OrderGroup.objects.create(
            user=user,
            shipping_address=address,
            **kwargs
        )

        return order_group

    return create_order_group


@pytest.fixture
def order_factory():
    """
    Factory to create order for each shopowner.
    """
    def create_order(group, shop, **kwargs):
        return Order.objects.create(
            group=group,
            shop=shop,
            shop_name=shop.name,
            total_amount=kwargs.pop("total_amount", 0),
            **kwargs
        )
    return create_order


@pytest.fixture
def order_item_factory():
    """
    Factory to create order item for an order.
    """
    def create_order_item(order, product, quantity=1):
        return OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_description=product.description,
            quantity=quantity,
            price=product.price
        )

    return create_order_item


@pytest.fixture
def populated_order_group_factory(customer_factory,
                                  order_group_factory,
                                  order_factory,
                                  order_item_factory,
                                  product_factory,
                                  shopowner_factory):
    """
    Creates an order group with orders and items.
    """

    def create_populated_order_group(user=None, **kwargs):
        user = user or customer_factory()
        shop = kwargs.pop("shop", shopowner_factory().owned_shop)
        group = kwargs.pop("group", order_group_factory(user=user))
        orders_per_group = kwargs.pop("orders_per_group", 1)
        items_per_order = kwargs.pop("items_per_order", 1)
        for _ in range(orders_per_group):
            order = order_factory(group=group, shop=shop)
            for _ in range(items_per_order):
                product = product_factory(shop=shop)
                order_item_factory(order=order, product=product)
        return group

    return create_populated_order_group
