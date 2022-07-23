from django.contrib import admin

from .models import Tag, Ingredient, Recipe, ShoppingCart, Favorite


@admin.register(Tag)
class AdminTag(admin.ModelAdmin):
    list_display = ('id', 'name', 'color')


@admin.register(Ingredient)
class AdminIngredient(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


@admin.register(Recipe)
class AdminRecipe(admin.ModelAdmin):
    list_display = ('author', 'name', 'cooking_time')
    list_filter = ('author', 'name')


@admin.register(ShoppingCart)
class AdminShoppingCart(admin.ModelAdmin):
    list_display = ('user', 'recipe')


@admin.register(Favorite)
class AdminFavorite(admin.ModelAdmin):
    list_display = ('user', 'recipe')
