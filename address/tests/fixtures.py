from django.conf import settings
from unittest.mock import patch, MagicMock

import io
import json
import pytest

from . import FAKE_LOCATION_DATA

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
