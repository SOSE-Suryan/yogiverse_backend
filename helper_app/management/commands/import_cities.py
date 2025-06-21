import csv
from django.core.management.base import BaseCommand
from helper_app.models import CitiesModel, CountryModel, StatesModel

class Command(BaseCommand):
    help = 'Import or update cities from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Yogiverse\management_media\CitiesModel-2025-06-21.csv')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        created_count = 0
        updated_count = 0
        skipped_count = 0
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    country_obj = CountryModel.objects.get(pk=row['country'])
                    state_obj = StatesModel.objects.get(pk=row['state'], country=country_obj)
                except CountryModel.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Country with id {row['country']} not found. Skipping row."))
                    skipped_count += 1
                    continue
                except StatesModel.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"State with id {row['state']} and country {row['country']} not found. Skipping row."))
                    skipped_count += 1
                    continue

                is_active = str(row.get('is_active', '1')) in ['1', 'True', 'true']

                city, created = CitiesModel.objects.update_or_create(
                    name=row['name'].strip(),
                    country=country_obj,
                    state=state_obj,
                    defaults={'is_active': is_active}
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {created_count} new cities, updated {updated_count} cities, skipped {skipped_count} rows.'
        ))
