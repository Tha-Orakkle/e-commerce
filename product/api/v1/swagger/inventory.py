from rest_framework import serializers

from common.swagger import (
    ForbiddenSerializer,
    make_error_schema_response,
    make_success_schema_response,
    make_not_found_error_schema_response,
    make_unauthorized_error_schema_response
)
from product.api.v1.serializers import InventorySerializer

# UPDATE INVENTORY SCHEMA

class InventoryRequestData(serializers.Serializer):
    """
    Serializer for the request data to update inventory.
    """
    action = serializers.CharField(default='add')
    quantity = serializers.IntegerField(default=36)


update_inventory_errors =  {
    'invalid_action': 'Provide a valid action: \'add\' or \'subtract\'.',
    'Invalid_quantity': 'Provide a valid quantity that is greater than 0.',
    'insufficient_inventory': 'Insufficient stock to complete this operation. Only <stock> left.'
}

update_inventory_schema = {
    'summary': 'Update a product inventory',
    'description': 'Adds and/or subtracts from a product inventory stock. \
        The action to be performed will be passed to the request body. \
        Product quantity must be greater than 0 but less than the total stock.',
    'tags': ['Inventory'],
    'request': InventoryRequestData,
    'responses': {
        200: make_success_schema_response(
            "Inventory updated successfully.",
            InventorySerializer
        ),
        400: make_error_schema_response(errors=update_inventory_errors),
        401: make_unauthorized_error_schema_response(),
        403: ForbiddenSerializer,
        404: make_not_found_error_schema_response(['product'])
    }
}
