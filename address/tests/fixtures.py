from unittest.mock import patch, MagicMock

import io
import json
import pytest

from . import FAKE_LOCATION_DATA

@pytest.fixture
def fake_location_file(tmp_path, settings):
    """
    Create a temporary file with fake location data for testing.
    """
    file_path = tmp_path / 'locations.json'
    data = FAKE_LOCATION_DATA
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    settings.GEODATA_FILE = file_path  # Override the GEODATA_FILE setting for tests
    return file_path


@pytest.fixture
def load_locations(django_db_setup, django_db_blocker, tmp_path, settings):
    """
    Load test location dataset into the database.
    """
    file_path = tmp_path / 'locations.json'
    settings.GEODATA_FILE = file_path
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
