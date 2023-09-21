from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

TEXT_CUT = 50


class Recipe(models.Model):
    """Recipe model."""

    name = models.CharField(
        max_length=128,
        verbose_name='Recipe name',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Publication Author',
    )
    image = models.ImageField(
        upload_to='media/%Y%m%d',
        verbose_name='Image',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ingredients',
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Tags',
    )
    text = models.TextField(
        blank=False,
        verbose_name='Recipe Description',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(120),),
        verbose_name='Cook Time',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Publication Date',
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        return self.text[:TEXT_CUT]


class Ingredient(models.Model):
    """Ingredient model."""

    name = models.CharField(
        max_length=128,
        verbose_name='Ingredient Name',
    )
    measurement_unit = models.CharField(
        max_length=32,
        verbose_name='Measure',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'

    def __str__(self):
        return self.name[:TEXT_CUT]


class RecipeIngredient(models.Model):
    """RecipeIngredient model."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ingredient',
    )
    product = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ingredient',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Amount',
    )

    class Meta:
        ordering = ('product',)
        verbose_name = 'Ingredients'
        verbose_name_plural = 'Ingredients'
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'product', 'amount'),
                name='unique_recipe'
            ),
        )

    def __str__(self):
        return f'Product {self.product} with {self.amount} in {self.recipe}'


class Tag(models.Model):
    """Tag model."""

    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Tag',
    )
    color = models.CharField(
        default='#ffffff',
        max_length=7,
        verbose_name='Tag Color',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Tag Slug',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name[:TEXT_CUT]


class Favorite(models.Model):
    """Favorite model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Favorites',
    )
    add_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date Add to Falourites',
    )

    class Meta:
        ordering = ('-add_date',)
        verbose_name = 'Favorites'
        verbose_name_plural = 'Favorites'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_recipe'
            ),
        )

    def __str__(self):
        return f'Recipe {self.recipe} in favorites of {self.user}'


class ShoppingCart(models.Model):
    """ShoppingCart model."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='User',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='recipe',
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_list_recipe'
            ),
        )

    def __str__(self):
        return f'Recipe {self.recipe} in shopping_cart of {self.user}'
