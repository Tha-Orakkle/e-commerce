from django.core.management.base import BaseCommand
from tqdm import tqdm

import ijson
import json

from . import GEODATA_FILE
from address.models import Country, State, City


# This program will simply import NG data to minimize db usage

class Command(BaseCommand):
    help = "Import geodata to the database."

    def handle(self, *args, **kwargs):
        if not GEODATA_FILE.exists():
            self.stdout.write(self.style.NOTICE("Geodata file does not exist."))
            self.stdout.write(self.style.NOTICE("Run\n\n   python manage.py fetch_geodata\nto download it.\n"))
            return
        
        tqdm_args = {
            'desc': 'Processing',
            'unit': 'items',
            'dynamic_ncols': True,
            'mininterval': 0.3
        }

        metadata_file = GEODATA_FILE.with_suffix('.meta.json')
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                total = metadata.get('items_saved', 0)
        if total:
            tqdm_args['total'] = total

        # access geodata file
        self.stdout.write("Importing geodata to the database.")
        self.stdout.write("This may take a while...")

        with open(GEODATA_FILE, 'r', encoding='utf-8') as f:
            objects = ijson.items(f, 'item')

            for obj in tqdm(objects, **tqdm_args):
                if obj.get('name') != 'Nigeria':
                    continue
                # Create country if it doesnt exists
                country, _ = Country.objects.get_or_create(
                    code=obj['iso2'],
                    defaults={'name': obj['name']}
                )

                # fetch existing data
                
                existing_states = {
                    s.name: s for s in State.objects.filter(country=country)
                }
                existing_cities = {
                    (c.name, c.state.id) : True
                    for c in City.objects.select_related('state').filter(state__country=country)
                }
                new_states = []
                new_cities = []


                for st in obj.get('states', []):
                    state_name = st['name']
                    state = existing_states.get(state_name)
                    if not state:
                        state = State(name=st['name'], country=country)
                        new_states.append(state)
                        existing_states[state_name] = state

                # create new states and update existing_states
                if new_states:
                    State.objects.bulk_create(new_states, ignore_conflicts=True)
                    for s in State.objects.filter(country=country):
                        existing_states[s.name] = s

                for st in obj.get('states', []):
                    state = existing_states.get(st['name'])
                    if not state:
                        continue
                    for c in st.get('cities', []):
                        if (c['name'], state.id) not in existing_cities:
                            new_cities.append(City(name=c['name'], state=state))
                            existing_cities[(c['name'], state.id)] = True
                if new_cities:
                    City.objects.bulk_create(new_cities, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS("Geodata imported to DB successfully.\n"))
