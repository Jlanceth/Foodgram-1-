from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Sum, Exists, OuterRef
from django.http import HttpResponse
from djoser.views import UserViewSet as DjoserUserViewSet
import pyshorteners

from api.serializers import TagSerializer, IngredientSerializer
from recipes.models import (
    Tag, Ingredient, Recipe, Favorite,
    ShopCard, RecipeIngredient
)
from user.models import Subscribe, User
from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReaderOrAuthenticated
from api.serializers import (
    ShoppingCartSerializer, FavoriteSerializer,
    RecipeSerializer, RecipeMakeSerializer,
    FavShopSerializer, CustomUserSerializer,
    SubscriptionsSerializers, RecipeSubSerializer,
    SubscriptionActionSerializer,
)
from .pagination import CustomLimitOffsetPagination
from .utils import generate_pdf


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrReaderOrAuthenticated]
    pagination_class = CustomLimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients'
        )

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(user=user, recipe=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShopCard.objects.filter(user=user, recipe=OuterRef('pk'))
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'partial_update' or self.action == 'create':
            return RecipeMakeSerializer
        return RecipeSerializer

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_short_link(self, request, pk):
        shortener = pyshorteners.Shortener()
        short_url = shortener.tinyurl.short(
            request.build_absolute_uri()
            .replace('/api', '')
            .replace('/get-link/', '')
        )
        return Response({'short-link': short_url})

    @action(
        detail=True, methods=['post', 'delete'],
        url_path='favorite',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'recipe': recipe.id}, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(FavShopSerializer(
                recipe, context={'request': request}
            ).data, status=status.HTTP_201_CREATED)

        favorite = Favorite.objects.filter(user=user, recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не находится у вас в избранном.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True, methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id}, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            ShopCard.objects.create(user=user, recipe=recipe)
            return Response(RecipeSubSerializer(
                recipe, context={'request': request}
            ).data, status=status.HTTP_201_CREATED)

        shop_cart = ShopCard.objects.filter(user=user, recipe=recipe)
        if shop_cart.exists():
            shop_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'errors': 'Рецепт не находится у вас в списке покупок.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False, methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_cart(self, request):
        user = request.user
        rec_in_cart = ShopCard.objects.filter(user=user).prefetch_related(
            'recipe__ingredients'
        )
        if not rec_in_cart.exists():
            return Response(
                {"detail": "Корзина пуста"},
                status=status.HTTP_200_OK
            )
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=rec_in_cart.values_list(
                'recipe', flat=True)
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        pdf_output = generate_pdf(ingredients)
        response = HttpResponse(pdf_output, content_type='application/pdf')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.pdf"'
        )
        return response


class CustomUserViewSet(DjoserUserViewSet):
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return super().get_serializer_class()
        return CustomUserSerializer

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated]
    )
    def set_avatar(self, request, *args, **kwargs):
        user = request.user

        if request.method == 'PUT':
            serializer = self.get_serializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': serializer.data.get('avatar')})

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = SubscriptionActionSerializer(
                data=request.data,
                context={'request': request, 'view': self}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscribe.objects.filter(user=user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': 'Вы не подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(subscriptions)
        serializer = SubscriptionsSerializers(
            pages,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)
