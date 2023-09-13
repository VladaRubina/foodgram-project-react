from django.contrib import admin

from .models import Favourite, Ingredient, Recipe, Tag
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class RecipeIngredientsInLine(admin.TabularInline):
    """RecipeIngredients embedded edition class."""

    model = Recipe.ingredients.through
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """RecipeAdmin class."""

    list_display = ('name', 'author', 'favourite_count',)
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-filter-'
    inlines = (RecipeIngredientsInLine,)

    def favourite_count(self, obj):
        return obj.favourites.count()


class IngredientResource(resources.ModelResource):
    """IngredientResource for download data class."""

    class Meta:
        model = Ingredient


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    """IngredientAdmin class."""

    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)
    empty_value_display = '-filter-'
    resource_class = IngredientResource


admin.site.register(Favourite)
admin.site.register(Tag)
