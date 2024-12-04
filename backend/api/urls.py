from rest_framework.routers import DefaultRouter
from django.urls import include, path

from api.views import (
    TagViewSet, IngredientViewSet,
    CustomUserViewSet, RecipeViewSet
)


v1_router = DefaultRouter()

v1_router.register(r'tags', TagViewSet, basename='tags')
v1_router.register(r'ingredients', IngredientViewSet, basename='ingredients')
v1_router.register(r'users', CustomUserViewSet, basename='users')
v1_router.register(r'recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('auth/', include('djoser.urls')),
    path('', include(v1_router.urls)),
]
