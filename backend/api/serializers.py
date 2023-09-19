from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserCreateSerializer, UserSerializer

from recipes.models import (ShoppingCart, Favourite, Ingredient,
                            Recipe, RecipeIngredient, Tag
                            )
from users.models import User, Follow


class UserSerializer(UserSerializer):
    """User serializer."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.subscribers.exists()
        return False

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )


class UserCreateSerializer(UserCreateSerializer):
    """User creation serializer."""

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'id',
            'first_name',
            'last_name',
            'password'
        )


class UserWithRecipesSerializer(UserSerializer):
    """User recipes serializer."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj)
        if 'recipes_limit' in self.context.get('request').GET:
            recipes_limit = self.context.get('request').GET['recipes_limit']
            author_recipes = author_recipes[:int(recipes_limit)]
        serializer = RecipeListSerializer(
            author_recipes,
            context={'request': self.context.get('request')},
            many=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )


class FollowSerializer(UserSerializer):
    """Follow user serializer."""

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        author = data.get('author')
        if user.pk == author.pk:
            raise exceptions.ValidationError(
                'Unable for self-subscription!'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise exceptions.ValidationError('Already subscripted!')
        return data

    class Meta:
        model = Follow
        fields = ('user', 'author')


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """RecipeIngredient Serializer."""

    id = serializers.StringRelatedField(source='product.id')
    name = serializers.ReadOnlyField(source='product.name')
    measurement_unit = serializers.ReadOnlyField(
        source='product.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateRecipeIngredientsSerializer(serializers.ModelSerializer):
    """CreateUpdateRecipeIngredient Serializer."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = Ingredient
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Tag Serializer."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Ingredient Serializer."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Recipe Serializer."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients'
    )
    is_favourited = serializers.SerializerMethodField(
        method_name='get_is_favourited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favourited(self, obj):
        return self.get_is_add(obj, Favourite)

    def get_is_in_shopping_cart(self, obj):
        return self.get_is_add(obj, ShoppingCart)

    def get_is_add(self, obj, add):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return add.objects.filter(user=user, recipe=obj).exists()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favuorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """RecipeCreateUpdate Serializer."""

    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1, max_value=120)

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Need to add at least one tag.'
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Need to add at least one ingredient.'
            )

        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'One recipe unable to have two same ingredients.'
                )

        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                product=get_object_or_404(Ingredient, pk=ingredient['id']),
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)

        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()

        recipe_ingredients = []
        for ingredient in ingredients:
            amount = ingredient['amount']
            ingredient = get_object_or_404(Ingredient, pk=ingredient['id'])
            recipe_ingredient = RecipeIngredient(
                recipe=instance,
                product=ingredient,
                amount=amount
            )
            recipe_ingredients.append(recipe_ingredient)
        RecipeIngredient.objects.bulk_create(
            recipe_ingredients, ignore_conflicts=True)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )

        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeListSerializer(serializers.ModelSerializer):
    """RecipeList Serializer."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class FavouriteSerializer(serializers.ModelSerializer):
    """Favourite Serializer."""

    class Meta:
        model = Favourite
        fields = 'id', 'user', 'recipe', 'add_date'
        validators = [
            UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=('user', 'recipe'),
                message='Already on favourites list!'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """ShoppingCart Serializer."""

    class Meta:
        model = ShoppingCart
        fields = 'id', 'user', 'recipe'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Already on purchase list!'
            )
        ]
