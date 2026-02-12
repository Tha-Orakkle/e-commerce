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
def country_factory():
    """
    Factory fixture for creating Country instances.
    """
    def create_country(name, code):
        return Country.objects.create(name=name, code=code)
    return create_country


@pytest.fixture
def state_factory():
    """
    Factory fixture for creating State instances.
    """
    def create_state(name, country):
        return State.objects.create(name=name, country=country)
    return create_state


@pytest.fixture
def city_factory():
    """
    Factory fixture for creating City instances.
    """
    def create_city(name, state):
        return City.objects.create(name=name, state=state)
    return create_city


@pytest.fixture
def country(country_factory):
    """
    Fixture for creating a Country instance.
    """
    return country_factory(name='Nigeria', code='NG')


@pytest.fixture
def state(state_factory, country):
    """
    Fixture for creating a State instance.
    """
    return state_factory(name='Lagos', country=country)


@pytest.fixture
def city(city_factory, state):
    """
    Fixture for creating a City instance.
    """
    return city_factory(name='Ikeja', state=state)


@pytest.fixture
def shipping_address_factory(city):
    def create_shipping_address(user, city=city):
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
