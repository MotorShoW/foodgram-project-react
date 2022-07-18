from django.db import models
from django.contrib.auth import get_user_model
from django.forms import CharField

User = get_user_model()


class Tag(models.Model):
    name = CharField(
        'Имя',
        max_length=200,
        required=True
    )
    color = models.CharField(
        'Цвет',
        max_length=7,
        required=True
    )
    slug = models.CharField(
        'Слаг',
        max_length=7,
        required=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipe'
    )
    ingredients = models.ManyToManyField(
        ''
    )
    name = models.CharField(
        'Имя рецета',
        max_length=200
    )
    image = models.ImageField(
        'Картинка',
        upload_to='',
        null=True,
        blank=True
    )
    text = models.TextField(
        'Текст рецепта'
    )
    cooking_time = models.IntegerField(
        'Время приготовления'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}, {self.author.username}'
