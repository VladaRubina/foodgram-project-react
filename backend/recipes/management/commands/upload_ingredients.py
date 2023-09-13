import csv

from pathlib import Path

from foodgram.settings import BASE_DIR
from recipes.models import Ingredient

from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

DATA_FILE_PATH = Path(Path(BASE_DIR, "data/"), "ingredients.csv")


class Command(BaseCommand):

    help = "Data upload from csv"

    def handle(self, *args, **options):
        headerList = ("name", "measurement_unit",)
        try:
            Ingredient.objects.get_or_create()
            self.stderr.write("Data uploaded..")
            return

        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

        self.stdout.write("Upload data")
        file = csv.DictReader(
            open(DATA_FILE_PATH, encoding="utf-8"), fieldnames=headerList
        )
        for row in file:
            data = Ingredient(
                name=row["name"], measurement_unit=row["measurement_unit"]
            )
            data.save()
