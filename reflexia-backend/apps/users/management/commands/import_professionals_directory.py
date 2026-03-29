import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.users.models import ProfessionalDirectoryEntry


class Command(BaseCommand):
    help = "Import the Catalonia professionals directory from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="apps/users/data/professionals_directory_catalonia.csv",
            help="Path to the CSV file to import.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file"])
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        created_count = 0
        updated_count = 0

        with file_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            required_columns = {"license_number", "complete_name"}
            if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
                raise CommandError("CSV must contain 'license_number' and 'complete_name' columns.")

            for row in reader:
                license_number = (row.get("license_number") or "").strip().upper()
                complete_name = (row.get("complete_name") or "").strip()

                if not license_number or not complete_name:
                    continue

                entry, created = ProfessionalDirectoryEntry.objects.update_or_create(
                    license_number=license_number,
                    defaults={"complete_name": complete_name},
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Created: {created_count}. Updated: {updated_count}."
            )
        )
