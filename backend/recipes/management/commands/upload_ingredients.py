import csv
from pathlib import Path

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.management.base import BaseCommand
from foodgram.settings import BASE_DIR
from recipes.models import Ingredient

DATA_FILE_PATH = Path(Path(BASE_DIR, "data/"), "ingredients.csv")


class Command(BaseCommand):

    help = "Data upload from csv"

    def handle(self, *args, **options):
        headerList = ("name", "measurement_unit",)
        try:
            self.stderr.write("Data uploaded..")
            return

        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

        self.stdout.write("Upload data")
        ingredients = []

        with open(DATA_FILE_PATH, 'r', encoding="utf-8") as csvfile:
            csvreader = csv.DictReader(csvfile, fieldnames=headerList)
            for row in csvreader:
                ingredients.append(
                    Ingredient(name=row["name"],
                    measurement_unit=row["measurement_unit"]
                    )
                )

        Ingredient.objects.bulk_create(ingredients)

        self.stdout.write("Data uploaded successfully.")
