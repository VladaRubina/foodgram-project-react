from django.conf import settings
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Cart, Favourite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from rest_framework import exceptions, serializers
from rest_framework.validators import UniqueTogetherValidator
from users.models import Follow, User


class UserSerializer(UserSerializer):
    """User serializer."""

    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and obj.subscribers.exists()

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

    def get_recipes(self, obj):
        author_recipes = Recipe.objects.filter(author=obj)

        recipes_limit = self.context.get('request').GET.get(
            'recipes_limit', settings.RECIPES_LIMIT_DEFAULT
        )
        author_recipes = author_recipes[:int(recipes_limit)]

        serializer = RecipeListSerializer(
            author_recipes,
            context={'request': self.context.get('request')},
            many=True
        )

        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(UserSerializer):
    """Follow user serializer."""

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        request = self.context.get('request')
        user = request.user
        author = data.get('author')
        if user == author:
            raise exceptions.ValidationError(
                'Unable for self-subscription!'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise exceptions.ValidationError('Already subscripted!')
        return data


class RecipeIngredientsSerializer(serializers.ModelSerializer):
    """RecipeIngredient Serializer."""

    id = serializers.StringRelatedField(source='product.id')
    name = serializers.CharField(source='product.name', read_only=True)
    measurement_unit = serializers.CharField(
    source='product.measurement_unit',
    read_only=True
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
    ingredients = serializers.SerializerMethodField()
    is_favourited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favourited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        serializer = RecipeIngredientsSerializer(ingredients, many=True)
        return serializer.data

    def get_is_favourited(self, obj):
        return self.get_is_add(obj, Favourite)

    def get_is_in_shopping_cart(self, obj):
        return self.get_is_add(obj, Cart)

    def get_is_add(self, obj, model):
        user = self.context['request'].user
        return not user.is_anonymous and \
            model.objects.filter(user=user, recipe=obj).exists()



class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """RecipeCreateUpdate Serializer."""

    author = UserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateRecipeIngredientsSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    def validate_tags(self, value):
        return value

    def validate_ingredients(self, value):
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

        recipe_ingredients = [
            RecipeIngredient(
                recipe=instance,
                product=get_object_or_404(Ingredient, pk=ingredient['id']),
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(
            recipe_ingredients, ignore_conflicts=True)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )

        return serializer.data


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


class CartSerializer(serializers.ModelSerializer):
    """Cart Serializer."""

    class Meta:
        model = Cart
        fields = 'id', 'user', 'recipe'
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Already on purchase list!'
            )
        ]
