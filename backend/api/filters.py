from django_filters import rest_framework as filters

from recipes.models import Ingredient, Tag
from recipes.models import Recipe


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name',
                              method='filter_by_name',)

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_by_name(self, queryset, name, value):
        if value:
            return queryset.filter(name__istartswith=value)
        return queryset


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')
