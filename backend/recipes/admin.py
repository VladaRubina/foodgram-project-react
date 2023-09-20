from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Favorite, Ingredient, Recipe, Tag


class RecipeIngredientsInLine(admin.TabularInline):
    """RecipeIngredients embedded edition class."""

    model = Recipe.ingredients.through
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """RecipeAdmin class."""

    list_display = ('name', 'author', 'favorite_count',)
    list_filter = ('author', 'name', 'tags',)
    empty_value_display = '-filter-'
    inlines = (RecipeIngredientsInLine,)

    def favorite_count(self, obj):
        return obj.favorites.count()


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


admin.site.register(Favorite)
admin.site.register(Tag)
