from django.conf import settings
from unittest.mock import patch, MagicMock

import io
import json
import pytest

from . import FAKE_LOCATION_DATA
from address.models import ShippingAddress, Country, State, City


@pytest.fixture(scope='session')
def test_locations_file_path(test_root_dir):
    """
    Create a file path for storing location dataset for testing.
    """
    original = getattr(settings, 'GEODATA_FILE', None)
    path = test_root_dir / 'locations'
    path.mkdir(exist_ok=True)
    
    file_path = path / 'locations.json'
    settings.GEODATA_FILE = file_path
    yield file_path
    
    if original is not None:
        settings.GEODATA_FILE = original
    else:
        delattr(settings, 'GEODATA_FILE')


@pytest.fixture(scope='session')
def load_locations_to_file(test_locations_file_path):
    """
    Create a temporary file with fake locations data for testing.
    """
    data = FAKE_LOCATION_DATA
    with open(test_locations_file_path, 'w') as f:
        json.dump(data, f, indent=2)
    yield test_locations_file_path


@pytest.fixture(scope='session')
def load_locations_to_db(django_db_setup, django_db_blocker, test_locations_file_path):
    """
    Load test location dataset into the database.
    """
    fake_api_res = FAKE_LOCATION_DATA
    
    with django_db_blocker.unblock():
        with patch('address.management.commands.fetch_geodata.requests.get') as mock_get:
            mock_res = MagicMock()
            mock_res.status_code = 200
            mock_res.headers = {'Content-Encoding': 'utf-8'}
            mock_res.raw = io.BytesIO(json.dumps(fake_api_res).encode('utf-8'))
            mock_get.return_value.__enter__.return_value = mock_res
            
            from django.core.management import call_command
            call_command('fetch_geodata', force=True)
            call_command('import_geodata')
    yield


@pytest.fixture
def shipping_address_factory(load_locations_to_db):
    def create_shipping_address(user):
        country = Country.objects.first()
        state = country.states.first()
        city = state.cities.first()
        count = user.addresses.count()

        return ShippingAddress.objects.create(
            user=user,
            city=city,
            full_name='John Doe',
            telephone='08112221111',
            street_address=f'{count + 1} Main St',
            postal_code='10001'
        )
    return create_shipping_address


@pytest.fixture
def create_shipping_address_data(load_locations_to_db):
    country = Country.objects.first()
    state = country.states.first()
    city = state.cities.first()
    return {
        'street_address': '123 Main St',
        'postal_code': '100001',
        'city': city.id,
        'state': state.id,
        'country': country.code,
        'full_name': 'Sheldon Cooper',
        'telephone': '08112223344',
    }