import django.contrib.auth.password_validation as validate
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from recipe.models import Tag, Ingredient, Recipe, IngredientAmount
from users.models import Subscription
from drf_base64.fields import Base64ImageField

User = get_user_model


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'password'
        )

    def validate_password(self, password):
        validate.validate_password(password)
        return password


class UserPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(label='Текущий пароль')
    new_password = serializers.CharField(label='Новый пароль')

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        if not authenticate(username=user.email, password=current_password):
            text = 'Проверьте правильность введенных данных'
            raise serializers.ValidationError(text, code='authorization')
        return current_password

    def validate_new_password(self, new_password):
        validate.validate_password(new_password)
        return new_password

    def create_password(self, validated_data):
        user = self.context['request'].user
        password = make_password(validated_data.get('new_password'))
        user.password = password
        user.save()
        return validated_data


class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name',
            'last_name', 'email', 'is_subscribed'
        )


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.follower.filter(following=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    author = RecipeUserSerializer(read_only=True,
                                  default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(required=True,
                                             many=True, source='recipe')
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_in_shopping_cart = serializers.BooleanField(read_only=True)
    is_favorited = serializers.BooleanField(read_onyl=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            IngredientAmount.objects.create(
                recipe=recipe,
                amount=ingredient.get('amount'),
                ingredient_id=ingredient.get('id')
            )

    def create(self, validated_data):
        validated_data.pop('recipe')
        ingredients = self.initial_data.pop('ingredients')
        tags = self.initial_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        validated_data.pop('recipe')
        ingredients = self.initial_data.pop('ingredients')
        tags = self.initial_data.pop('tags')
        if ingredients:
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)

        if tags:
            instance.tags.set(tags)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')
        ingredient_list = []

        for item in ingredients:
            ingredient = get_object_or_404(Ingredient, id=item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингредиент уже существует')
            ingredient_list.append(ingredient)

        if not tags:
            raise serializers.ValidationError('Укажите тег')

        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Так питаюсь только я')
        return ingredients

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) <= 0:
            raise serializers.ValidationError('Укажите время приготовления')
        return cooking_time


class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='following.id')
    username = serializers.CharField(source='following.username')
    email = serializers.EmailField(source='following.email')
    first_name = serializers.CharField(source='following.first_name')
    last_name = serializers.CharField(source='following.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscription
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'recipes', 'is_subscribed', 'recipes_count', 'recipes')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.following.recipe.all()[:int(limit)] if limit
            else obj.following.recipe.all()
        )
        return RecipeSubscriptionSerializer(recipes, many=True).data


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(label='Токен', read_only=True)
    email = serializers.CharField(label='Email', write_only=True)
    password = serializers.CharField(
        label='Пароль',
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)
            if not user:
                text = 'Проверьте правильность введенных данных'
                raise serializers.ValidationError(text, code='authorization')

        else:
            text = 'Заполните поля'
            raise serializers.ValidationError(text, code='authorization')

        data['user'] = user
        return data
