from rest_framework import serializers
from djoser.serializers import UserSerializer
from django.core.files.base import ContentFile
from rest_framework.fields import SerializerMethodField
import base64

from recipes.models import (
    Recipe, RecipeIngredient, Favorite, ShopCard,
    Tag, Ingredient
)
from user.models import User, Subscribe


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class CustomUserSerializer(UserSerializer):
    is_subscribed = SerializerMethodField(read_only=True)
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class SubscriptionsSerializers(CustomUserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes_count',
                                                     'recipes',)

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj).order_by('-id')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeSubSerializer(
            recipes, many=True,
            context={'request': request}
        ).data


class SubscriptionActionSerializer(serializers.Serializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate(self, data):
        user = self.context['request'].user
        author = self.context['view'].get_object()

        # Проверка, что пользователь пытается подписаться на самого себя
        if user == author:
            raise serializers.ValidationError(
                {'errors': 'Вы не можете подписаться на себя.'}
            )

        # Проверка, что подписка уже существует
        if Subscribe.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Вы уже подписаны на этого пользователя.'}
            )

        data['user'] = user
        data['author'] = author
        return data

    def create(self, validated_data):
        return Subscribe.objects.create(**validated_data)

    def to_representation(self, instance):
        author = self.context['view'].get_object()
        serializer = SubscriptionsSerializers(author, context=self.context)
        return serializer.data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class AddIngredientSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMakeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = AddIngredientSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        fields = ('tags', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')
        model = Recipe

    def _set_ingredients_and_tags(self, recipe, ingredients, tags):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )
        recipe.tags.set(tags)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Тэги должны быть уникальными.')
        if len(ingredients) != len({ingredient['id']
                                    for ingredient in ingredients}):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        author = self.context['request'].user
        recipe = Recipe.objects.create(author=author, **validated_data)
        self._set_ingredients_and_tags(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.ingredients.clear()
        self._set_ingredients_and_tags(instance, ingredients, tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    class Meta:
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )
        model = Recipe

    def get_ingredients(self, obj):
        queryset = obj.recipe_ingredients.all()
        return IngredientRecipeSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return ShopCard.objects.filter(user=user, recipe=obj).exists()
        return False


class FavShopSerializer(RecipeSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe',)

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже у вас в избранном.')
        return attrs


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopCard
        fields = ('recipe',)

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']
        if ShopCard.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже у вас в списке покупок.'
            )
        return attrs
