from .city import get_cities_schema
from .country import get_countries_schema
from .state import get_states_schema
from .shipping_address import (
    get_shipping_addresses_schema,
    get_shipping_address_schema,
    post_shipping_address_schema,
    patch_shipping_address_schema,
    delete_shipping_address_schema
)


__all__ = [
    # location
    'get_cities_schema',
    'get_countries_schema',
    'get_states_schema',

    # shipping address
    'post_shipping_address_schema',
    'delete_shipping_address_schema',
    'get_shipping_addresses_schema',
    'get_shipping_address_schema',
    'patch_shipping_address_schema',
]