import django_filters
from django.core.exceptions import ValidationError
from django_filters.fields import MultipleChoiceField

from recipe.models import Ingredient, Recipe
from users.models import User


class TagMultipleChoiceField(MultipleChoiceField):
    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'],
                code='required'
                )
        for item in value:
            if item in self.choices and not self.valid_value(item):
                raise ValidationError(
                    self.error_messages['invalid_choice'],
                    code='invalid_choice',
                    params={'value': item}
                )


class TagFilter(django_filters.AllValuesFilter):
    field_class = TagMultipleChoiceField


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    tag = TagFilter(field_name='tag')
    is_favorited = django_filters.BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = django_filters.BooleanFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tag', 'is_favorited', 'is_in_shopping_cart')


class IngrediendFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='isstartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
