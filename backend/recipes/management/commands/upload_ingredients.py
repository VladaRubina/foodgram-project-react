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
        headerList = ("name", "measurement_unit")

        if Ingredient.objects.exists():
            self.stderr.write("Data uploaded..")
            return

        self.stdout.write("Upload data")

        file = csv.DictReader(
            open(DATA_FILE_PATH, encoding="utf-8"), fieldnames=headerList
        )

        ingredient_list = [
            Ingredient(name=row["name"], measurement_unit=row["measurement_unit"])
            for row in file
        ]

        Ingredient.objects.bulk_create(ingredient_list)

        self.stdout.write("Data uploaded successfully")