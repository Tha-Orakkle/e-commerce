from unittest.mock import patch, MagicMock

import io
import json

from . import FAKE_LOCATION_DATA
from address.models import Country, State, City


def test_fetch_geodata_creates_file(test_locations_file_path, settings):
    """
    Test that the fetch_geodata command fetches data and
    creates the geodata file when it doesn't exist.
    """
    fake_api_res = FAKE_LOCATION_DATA
    with patch('address.management.commands.fetch_geodata.requests.get') as mock_get:
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.headers = {'Content-Encoding': 'utf-8'}
        mock_res.raw = io.BytesIO(json.dumps(fake_api_res).encode('utf-8'))
        mock_get.return_value.__enter__.return_value = mock_res
        
        from django.core.management import call_command
        call_command('fetch_geodata', force=True)
        
    assert settings.GEODATA_FILE.exists(), "Geodata file should be created after fetching."
    
    with open(test_locations_file_path, 'r') as f:
        data = json.load(f)
        assert data == fake_api_res, "The content of the geodata file should match the fake API response."


def test_import_geodata(db_access, load_locations_to_file):
    """
    Test the import_geodata command to ensure it 
    correctly imports data from the fake location file.
    """
    assert not Country.objects.exists(), "No countries should exist before import."
    from django.core.management import call_command
    call_command('import_geodata')
    
    # Verify that the data was imported correctly
    assert Country.objects.filter(code='NG').exists(), "Nigeria should be imported as a country."
    nig = Country.objects.get(code='NG')
    assert nig.name == 'Nigeria', "Country name should be 'Nigeria'."
    
    assert State.objects.filter(name='Lagos', country=nig).exists(), "Lagos state should be imported."
    lag = State.objects.get(name='Lagos', country=nig)
    
    assert City.objects.filter(name='Ikeja', state=lag).exists(), "Ikeja city should be imported."
    assert City.objects.filter(name='Lekki', state=lag).exists(), "Lekki city should be imported."
    assert City.objects.filter(name='Yaba', state=lag).exists(), "Yaba city should be imported."
    

