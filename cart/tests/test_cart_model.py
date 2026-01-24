from cart.models import Cart, CartItem

import pytest

from common.exceptions import ErrorException

# from product.tests.conftest import product, inventory


def test_cart_model_creation(customer_no_cart):
    """
    Test cart creation with model.
    """
    assert not Cart.objects.filter(user=customer_no_cart).exists()

    cart = Cart.objects.create(user=customer_no_cart)
    assert Cart.objects.filter(user=customer_no_cart).exists()
    assert cart.id is not None
    assert cart.user == customer_no_cart
    

def test_cart_string_representation(customer_no_cart):
    """
    Test cart object string representation.
    """
    cart = Cart.objects.create(user=customer_no_cart)
    
    assert str(cart) == f"<Cart: {cart.id}>" 


def test_add_item_to_cart(customer, product, inventory):
    """
    Test adding product to a cart.
    """
    assert inventory.stock == 20
    
    cart = customer.cart
    assert not cart.items.exists()
    
    cart.add_to_cart(product, 10)
    
    assert cart.items.count() == 1
    assert cart.items.filter(product=product).exists()
    item = cart.items.first()
    assert item.quantity == 10
    
    
def test_add_item_duplicate_item_to_cart(customer, product, inventory):
    """
    Test that duplicate product can not be added to the cart.
    Duplicate product replaces the former including the qty.
    """
    assert inventory.stock == 20
    
    cart = customer.cart
    cart.add_to_cart(product, 10)
    assert cart.items.filter(product=product).exists()
    item = cart.items.first()
    assert item.quantity == 10
    
    cart.add_to_cart(product, 15)
    assert cart.items.count() == 1
    item.refresh_from_db()
    assert item.quantity == 15
    
    
def test_add_item_that_is_out_of_stock_to_cart(customer, product):
    """
    Test adding an out-of-stok product to cart.
    """
    cart = customer.cart
    
    with pytest.raises(ErrorException) as exc:
        cart.add_to_cart(product, 20)
    assert exc.value.detail == "Product out of stock."
    assert exc.value.code == "out_of_stock"
    assert exc.value.status_code == 400
    
    
def test_remove_item_from_cart(customer, product, inventory):
    """
    Test remove an item from cart.
    """
    cart = customer.cart
    cart.add_to_cart(product, 15)
    
    assert cart.items.filter(product=product).exists()
    item = cart.items.first()
    cart.remove_from_cart(item)
    
    assert cart.items.count() == 0
    assert not cart.items.filter(product=product).exists()


def test_check_cart_item_availability(customer, shopowner, product_factory):
    """
    Test method that checks for item availability before checkout.
    """
    prod_1 = product_factory(shop=shopowner.owned_shop)
    prod_1.inventory.add(20, handle='tester')
    prod_2 = product_factory(shop=shopowner.owned_shop)
    prod_2.inventory.add(20, handle='tester')
    prod_3 = product_factory(shop=shopowner.owned_shop)
    prod_3.inventory.add(20, handle='tester')

    cart = customer.cart
    cart.add_to_cart(prod_1, 15)
    cart.add_to_cart(prod_2, 15)
    cart.add_to_cart(prod_3, 15)

    assert cart.items.filter(product=prod_1).exists()
    assert cart.items.filter(product=prod_2).exists()


    with pytest.raises(ErrorException) as e:
        item_1 = cart.items.filter(product=prod_1).first()
        prod_1.delete()
        item_1.refresh_from_db()
        cart.check_item_availability(item_1)

    assert e.value.detail == "Product no longer available."
    assert e.value.code == "product_unavailable"
    assert e.value.status_code == 400
    
    with pytest.raises(ErrorException) as ee:
        item_2 = cart.items.filter(product=prod_2).first()
        prod_2.is_active = False
        prod_2.save(update_fields=['is_active'])
        cart.check_item_availability(item_2)

    assert ee.value.detail == "Product no longer available."
    assert ee.value.code == "product_unavailable"
    assert ee.value.status_code == 400
    
    item_3 = cart.items.filter(product=prod_3).first()
    assert cart.check_item_availability(item_3)


def test_increment_item_quantity(customer, product, inventory):
    """
    Test incrementing cart item quantity.
    Qty increments by 1.
    """
    cart = customer.cart
    cart.add_to_cart(product, 19)
    
    item = cart.items.first()
    
    assert item.quantity == 19
    
    cart.increment_item_quantity(item)
    assert item.quantity == 20

    with pytest.raises(ErrorException) as e:
        cart.increment_item_quantity(item) # only 20 items left in stock
    assert e.value.detail == f"Insufficient stock. Only {inventory.stock} left."
    assert e.value.code == "insufficient_stock"
    assert e.value.status_code == 400
    
    
def test_decrement_item_quantity(customer, product, inventory):
    """
    Test decrementing quantity of cart item.
    Qty decrements by 1 and removes item from cart when qty is 0.
    """
    
    cart = customer.cart
    cart.add_to_cart(product, 0)
    item = cart.items.first()
    
    # Test rare situation of where cart item is 0
    with pytest.raises(ErrorException) as e:
        cart.decrement_item_quantity(item)
    assert e.value.detail == "Cannot remove from item with 0 quantity."      
    assert e.value.code == "invalid_quantity"
    assert e.value.status_code == 400
    # check that the item is removed from the cart
    assert cart.items.count() == 0
    
    # Test valid decrement
    cart.add_to_cart(product, 2)
    item = cart.items.first()
    assert item.quantity == 2
    cart.decrement_item_quantity(item)
    item.refresh_from_db()
    assert item.quantity == 1
    
    # Test removing last qty 
    cart.decrement_item_quantity(item)
    assert cart.items.count() == 0
    assert not cart.items.exist()
