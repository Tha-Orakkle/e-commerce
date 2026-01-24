from django.contrib.auth import get_user_model

import pytest

from cart.models import CartItem

User = get_user_model()


def fill_customer_cart(cart, shop, product_factory, count):
    """
    Fills a customers cart and fill it with products.
    """
    items = []
    for _ in range(count):
        prd = product_factory(shop=shop)
        prd.inventory.add(20, handle='tester')
        items.append(
            CartItem(
                quantity=15,
                product=prd,
                product_name=prd.name,
                cart=cart
            )
        )
    CartItem.objects.bulk_create(items)
    cart.refresh_from_db()
    return cart


@pytest.fixture
def customer_no_cart(db):
    count = User.objects.filter(is_customer=True, is_superuser=False).count() + 1
    customer = User.objects.create_user(
        email=f"customer{count}@email.com",
        password="Password123#",
    )
    return customer