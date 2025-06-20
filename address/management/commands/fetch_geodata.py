from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from tqdm import tqdm # for progress bar

import gzip
import ijson
import json
import requests

from . import GEODATA_FILE, GEODATA_URL
# from address.models import GeodataImportLog


class Command(BaseCommand):
    help = f"Fetch geodata from {GEODATA_URL} to populate the Country, State and City tables."
    
    def handle(self, *args, **kwargs):
        """
        Gets the data.
        """
        count = 0

        if GEODATA_FILE.exists():
            self.stdout.write(self.style.WARNING("Geodata json file already exists. Do you want to update it? (y/n)"))
            user_input = input("> ").strip().lower()
            if user_input != 'y':
                self.stdout.write(self.style.NOTICE("Using existing geodata file. No changes made.\n"))
                return

        # Get the geodata remotely
        try:
            self.stdout.write(f"\nFetching geodata from:")
            self.stdout.write(self.style.HTTP_INFO(f"{GEODATA_URL}\n"))
            self.stdout.write("This may take a while...\n")
            with requests.get(GEODATA_URL, stream=True, timeout=(5, 30)) as response:
                response.raise_for_status()
                raw = response.raw
                if response.headers.get('Content-Encoding') == 'gzip':
                    stream = gzip.GzipFile(fileobj=raw)
                else:
                    stream = raw
                objects = ijson.items(stream, 'item')
                with open(GEODATA_FILE, 'w') as f, tqdm(
                    desc="Downloading",
                    unit=" items",
                    dynamic_ncols=True,
                    mininterval=0.3
                ) as pbar:
                    f.write('[')
                    first = True
                    for obj in objects:
                        if not first:
                            f.write(',\n')
                        else:
                            first = False
                        f.write(json.dumps(obj))
                        count += 1
                        pbar.update(1)
                    f.write(']')

            # create a meta json file for the geodata
            with open(GEODATA_FILE.with_suffix('.meta.json'), 'w') as meta:
                json.dump({'filename': GEODATA_FILE.name, 'items_saved': count}, meta)
            
            self.stdout.write(self.style.SUCCESS(f"\nGeodata successfully saved to {GEODATA_FILE}."))
            self.stdout.write(self.style.SUCCESS(f"To import it into your database, run:\n\n    --python manage.py import_geodata\n"))

        except requests.exceptions.HTTPError as e:
            raise CommandError(f"HTTP error occurred: {e}")
        except requests.exceptions.ConnectionError as e:
            raise CommandError(f"Connection error occurred: {e}")
        except requests.exceptions.Timeout as e:
            raise CommandError(f"Request timed out: {e}")
        except requests.exceptions.RequestException as e:
            raise CommandError(f"Request error: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")
