from django.urls import path

from .views import (IngredientList, IngredientDetail, TagList, TagDetail,
                    RecipeList, RecipeDetail, FavoriteDetail, UserList,
                    UserDetail, AuthToken, SubscriptionList,
                    SubscriptionDetail, ShoppingCartDetail, set_password,
                    logout, download_shopping_cart)

urlpatterns = [
    path('auth/token/login/', AuthToken.as_view(), name='login'),
    path('auth/token/logout', logout, name='logout'),

    path('users', UserList.as_view(), name='user_list'),
    path('users/<int:pk>/', UserDetail.as_view(), name='user_detail'),
    path('users/subscriptions/', SubscriptionList.as_view(),
         name='subscription_list'),
    path('users/<int:user_id>/subscribe', SubscriptionDetail.as_view(),
         name='subscribe'),
    path('users/set_password/', set_password, name='set_password'),

    path('ingredients/', IngredientList.as_view(), name='ingredient_list'),
    path('ingredients/<int:pk>/', IngredientDetail.as_view(),
         name='ingredient_detail'),

    path('tags/', TagList.as_view(), name='tag_list'),
    path('tags/<int:pk>/', TagDetail.as_view(), name='tag_detail'),

    path('recipes/', RecipeList.as_view(), name='recipe_list'),
    path('recipes/<int:pk>/', RecipeDetail.as_view(), name='recipe_detail'),
    path('recipes/<int:recipe_id>/favorite/', FavoriteDetail.as_view(),
         name='recipe_favorite'),
    path('recipe/<int:recipe_id/shopping_cart/', ShoppingCartDetail.as_view(),
         name='shopping_cart'),
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name='download_shopping_cart')
]
