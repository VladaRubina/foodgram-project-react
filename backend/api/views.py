from django.db import models
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from foodgram.pagination import CustomPagination
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User

from api.filters import IngredientFilter, RecipiesFilter
from api.permissions import RecipePermission
from api.serializers import (FavoriteSerializer, FollowSerializer,
                             IngredientSerializer,
                             RecipeCreateUpdateSerializer,
                             RecipeListSerializer, RecipeSerializer,
                             ShoppingCartSerializer, TagSerializer,
                             UserWithRecipesSerializer)


class UserViewSet(UserViewSet):
    """User ViewSet."""

    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPagination

    @action(
        detail=False,
        methods=('GET',),
        serializer_class=UserWithRecipesSerializer,
        permission_classes=(IsAuthenticated, )
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(subscribers__user=request.user)
        paginated_queryset = self.paginate_queryset(queryset)
        serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        serializer_class=UserWithRecipesSerializer
    )
    def subscribe(self, request, id=None):
        user = self.request.user
        author = get_object_or_404(User, pk=id)
        if self.request.method == 'POST':
            context = {'request': request}
            data = {
                'user': user.id,
                'author': author.pk
            }
            serializer = FollowSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        subscription = get_object_or_404(
            Follow,
            user=user,
            author=author,
        )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Recipe ViewSet."""

    queryset = Recipe.objects.all()
    permission_classes = (RecipePermission,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipiesFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def favorite_logic(self, user, recipe):
        serializer = FavoriteSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        favorite_serializer = RecipeListSerializer(recipe)
        return favorite_serializer.data

    @action(detail=True, methods=('POST', 'DELETE'))
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            favorite_data = self.favorite_logic(user, recipe)
            return Response(
                favorite_data,
                status=status.HTTP_201_CREATED
            )
        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite:
            raise exceptions.ValidationError(
                'The recipe is not in list of favorites!'
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def shopping_cart_logic(self, user, recipe):
        serializer = ShoppingCartSerializer(
            data={'user': user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        shopping_cart_serializer = RecipeListSerializer(recipe)
        return shopping_cart_serializer.data

    @action(detail=True, methods=('POST', 'DELETE'))
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            shopping_cart_data = self.shopping_cart_logic(user, recipe)
            return Response(
                shopping_cart_data,
                status=status.HTTP_201_CREATED
            )
        shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not shopping_cart:
            raise exceptions.ValidationError(
                'The recipe is not in list of shopping_cart!'
            )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('GET',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        ingredients = (
            RecipeIngredient.objects.filter(recipe_id__in=recipes)
            .values("product_id__name", "product_id__measurement_unit")
            .annotate(models.Sum("amount"))
        )
        purchase_list_text = 'Purchase list:\n\n'
        for item in ingredients:
            purchase_list_text += (
                f'{item["product_id__name"]}, {item["amount__sum"]} '
                f'{item["product_id__measurement_unit"]}\n'
            )
        response = HttpResponse(purchase_list_text, content_type='text/plain')
        response['content-disposition'] = (
            'attachment; filename=purchase_list.txt'
        )
        return response


class IngredientViewSet(viewsets.ModelViewSet):
    """Ingredient ViewSet."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_class = (RecipePermission,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ModelViewSet):
    """Tag ViewSet."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_class = (IsAuthenticatedOrReadOnly)
    pagination_class = None
