from django.contrib.auth import get_user_model

import pytest

from cart.models import CartItem

User = get_user_model()


@pytest.fixture
def create_cart_items(product_factory):
    """
    Factory to create cart items for a given cart.
    """
    def _create(cart, shops, num_items=3, quantity=10):
        total = 0
        products = []

        for i in range(num_items):
            shop = shops[i % len(shops)]
            product = product_factory(shop=shop)
            product.inventory.add(qty=20, handle=f'test-{i}')
            cart.add_to_cart(product, quantity=quantity)
            total += product.price * quantity
            products.append(product)

        return total, products

    return _create


@pytest.fixture
def customer_no_cart(db):
    count = User.objects.filter(is_customer=True, is_superuser=False).count() + 1
    customer = User.objects.create_user(
        email=f"customer{count}@email.com",
        password="Password123#",
    )
    return customer