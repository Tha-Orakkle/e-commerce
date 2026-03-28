import pytest


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