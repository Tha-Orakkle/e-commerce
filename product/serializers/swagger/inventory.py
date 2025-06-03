from drf_spectacular.utils import OpenApiParameter

from common.swagger import (
    get_success_response,
    get_error_response_with_examples,
    get_error_response,
    UnauthorizedSerializer,
    ForbiddenSerializer
)
from drf_spectacular.utils import OpenApiResponse, OpenApiExample



examples =  {
    'Invalid action': 'Invalid action.',
    'Invalid quantity': "Provide a valid quantity that is greater than 0.",
    'Insufficient inventory': "Insufficient inventory."
}

update_inventory_schema = {
    'summary': 'Update a product inventory',
    'description': 'Adds and/or subtracts from a product inventory stock. \
        The action to be performed will be passed as a query string parameter. \
        Product quantity must be greater than 0 but less than theh total stock.',
    'tags': ['Inventory'],
    'parameters': [OpenApiParameter(
        name='action',
        type=str,
        description="Could be 'add' or 'subtract'",
        required=True
    )],
    'request': None,
    'responses': {
        200: get_success_response("Inventory updated successfully."),
        400: get_error_response_with_examples(examples),
        401: UnauthorizedSerializer,
        403: ForbiddenSerializer,
        404: get_error_response("Product not found.", 404)
    }
}
