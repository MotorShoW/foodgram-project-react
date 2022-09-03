from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.db.models.expressions import OuterRef, Value, Exists
from django.db.models.aggregates import Count, Sum
from rest_framework.response import Response
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont


from .serializers import (UserListSerializer, UserCreateSerializer,
                          UserPasswordSerializer, SubscriptionSerializer,
                          IngredientSerializer, TagSerializer,
                          RecipeSerializer, TokenSerializer,
                          RecipeSubscriptionSerializer)
from .permissions import IsAuthorOrAdminOrReadOnly
from .filters import RecipeFilter, IngrediendFilter
from recipe.models import Ingredient, Recipe, Favorite, Tag, ShoppingCart


User = get_user_model


class IngredientList(generics.ListAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngrediendFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientDetail(generics.RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)


class TagList(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class TagDetail(generics.RetrieveAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class RecipeList(generics.ListCreateAPIView):
    serializer_class = RecipeSerializer
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Value(False),
                is_in_shopping_cart=Value(False),
            ).select_related(
                'author'
            ).prefetch_related(
                'shopping_cart', 'ingredients', 'recipe',
                'tags', 'favorite_recipe'
            )

        return Recipe.objects.annotate(
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=self.request.user, recipe=OuterRef('id')
            )),
            is_favorited=Exists(Favorite.objects.filter(
                user=self.request.user, recipe=OuterRef('id')
            ))
        ).select_related(
            'author'
        ).prefetch_related(
            'shopping_cart', 'ingredients', 'recipe',
            'tags', 'favorite_recipe'
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RecipeDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Recipe.objects.annotate(
                is_favorited=Value(False),
                is_in_shopping_cart=Value(False),
            ).select_related(
                'author'
            ).prefetch_related(
                'shopping_cart', 'ingredients', 'recipe',
                'tags', 'favorite_recipe'
            )

        return Recipe.objects.annotate(
            is_favorited=Exists(Favorite.objects.filter(
                user=self.request.user, recipe=OuterRef('id')
            )),
            is_in_shopping_cart=Exists(Favorite.objects.filter(
                user=self.request.user, recipe=OuterRef('id')
            ))
        ).select_related(
            'author'
        ).prefetch_related(
            'shopping_cart', 'ingredients', 'recipe',
            'tags', 'favorite_recipe'
        )


class FavoriteDetail(generics.RetrieveDestroyAPIView):
    serializer_class = RecipeSubscriptionSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class UserList(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.annotate(is_subscribed=Value(False))

        return User.objects.annotate(
            is_subscribed=Exists(self.request.user.follower.filter(
                following=OuterRef('id')
            ))
        ).prefetch_related('follower', 'following')

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)


class UserDetail(generics.RetrieveAPIView):
    serializer_class = UserListSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return User.objects.annotate(is_subscribed=Value(False))

        return User.objects.annotate(
            is_subscribed=Exists(self.request.user.follower.filter(
                following=OuterRef('id')
            ))
        ).prefetch_related('follower', 'following')


class AuthToken(ObtainAuthToken):
    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key},
                        status=status.HTTP_201_CREATED)


class SubscriptionList(generics.ListAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            is_subscribed=Value(True),
            recipes_count=Count('following__recipe')
        )


class SubscriptionDetail(generics.RetrieveDestroyAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return self.request.user.follower.select_related(
            'following'
        ).prefetch_related(
            'following__recipe'
        ).annotate(
            is_subscribed=Value(True),
            recipes_count=Count('following__recipe')
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user.follower.filter(following=instance).exists():
            return Response(
                {'errors': 'Подписка уже оформлена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.id == instance.id:
            return Response(
                {'errors': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = request.user.follower.create(following=instance)
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        user_id = self.kwargs['user_id']
        user = get_object_or_404(id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def perform_destroy(self, instance):
        self.request.user.follower.filter(following=instance).delete()


class ShoppingCartDetail(generics.RetrieveDestroyAPIView):
    serializer_class = RecipeSubscriptionSerializer

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)


@api_view(['POST'])
def set_password(request):
    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    token = get_object_or_404(Token, user=request.user)
    token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def download_shopping_cart(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="yourcart.pdf"'
    p = canvas.Canvas(response)
    x = 50
    y = 800
    indent = 15
    shopping_cart = (
        request.user.shopping_cart.recipe.values(
            'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(total=Sum('recipe__amount')).order_by('total')
    )
    pdfmetrics.registerFont(TTFont('Vera', 'Vera.ttf', 'UTF-8'))
    if not shopping_cart:
        p.setFront('Vera', 20)
        p.drawString(x, y, 'Список пуст')
        p.save()
        return response

    p.setFont('Vera', 20)
    p.drawString(x, y, 'Список покупок :')
    p.setFont('Vera', 16)
    for i, recipe in enumerate(shopping_cart, start=1):
        p.drawString(
            x, y - indent, f'{i}. {recipe["ingredients__name"]} -'
            f'{recipe["amount"]} {recipe["ingredients__measurement_unit"]}.'
        )
        y -= 15
        if y <= 50:
            p.showPage()
            p.setFont('Vera', 16)
            y = 800
    p.save()
    return response
