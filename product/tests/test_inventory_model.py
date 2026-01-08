from product.models import Inventory

import pytest

from common.exceptions import ErrorException, InventoryDeletionError

def test_inventory_model_creation_with_product(product):
    """
    Test that inventory model is created correctly with product.
    """
    assert product.inventory is not None
    
def test_inventory_mode_string_representation(inventory):
    """
    Test the string representation of the inventory model.
    """
    expected_str = f"<Inventory: {inventory.id}> {inventory.product.name} - {inventory.stock} items"
    assert str(inventory) == expected_str

def test_inventory_model_stock_setter_getter(inventory):
    """
    Test that stock getter works and setter raises error.
    """
    assert inventory.stock == 20
    with pytest.raises(AttributeError) as exc_info:
        inventory.stock = 15
    assert "Direct assignment to stock is not allowed" in str(exc_info.value)


def test_inventory_model_stock_with_add_subtract_methods(inventory):
    """
    Test that stock is updated correctly with add and subtract methods.
    """

    assert inventory.stock == 20
    
    # Assuming add and subtract methods exist
    inventory.add(10, handle='tester2')
    assert inventory.stock == 30
    assert inventory.last_updated_by == 'tester2'

    inventory.subtract(5, handle='tester3')
    assert inventory.stock == 25
    assert inventory.last_updated_by == 'tester3'

def test_inventory_model_subtract_insufficient_stock(inventory):
    """
    Test that subtracting more than available stock raises error.
    """
    assert inventory.stock == 20

    with pytest.raises(ErrorException) as exc_info:
        inventory.subtract(25, handle='tester2')
    assert exc_info.value.code == 'insufficient_stock'
    detail = f"Insufficient stock to complete this operation. Only {inventory.stock} left."
    assert exc_info.value.detail == detail
    assert inventory.stock == 20

def test_inventory_model_subtract_negative_amount(inventory):
    """
    Test that subtracting negative amount raises error.
    """
    assert inventory.stock == 20

    with pytest.raises(ValueError) as exc_info:
        inventory.subtract(-5, handle='tester2')
    detail = "Provide a valid quantity that is greater than 0."
    assert detail == str(exc_info.value)
    assert inventory.stock == 20
    
def test_inventory_model_add_negative_amount(inventory):
    """
    Test that adding negative amount raises error.
    """
    assert inventory.stock == 20

    with pytest.raises(ValueError) as exc_info:
        inventory.add(-10, handle='tester2')
    detail = "Provide a valid quantity that is greater than 0."
    assert detail == str(exc_info.value)
    assert inventory.stock == 20
    
def test_inventory_model_last_updated_by_field(inventory):
    """
    Test that last_updated_by field is updated correctly.
    """
    assert inventory.last_updated_by == 'tester'

    inventory.add(5, handle='tester4')
    assert inventory.last_updated_by == 'tester4'

    inventory.subtract(3, handle='tester5')
    assert inventory.last_updated_by == 'tester5'
    
def test_inventory_delete_fails(inventory):
    """
    Test that deleting inventory instance raises error.
    """
    with pytest.raises(InventoryDeletionError) as exc_info:
        inventory.delete()
    detail = "Inventory instances cannot be deleted directly; use product deletion instead."
    assert detail == str(exc_info.value)
    

def test_that_inventory_is_deleted_with_product(product):
    """
    Test that inventory is deleted when the associated product is deleted.
    """
    inventory_id = product.inventory.id
    product.delete()
    with pytest.raises(Inventory.DoesNotExist):
        Inventory.objects.get(id=inventory_id)