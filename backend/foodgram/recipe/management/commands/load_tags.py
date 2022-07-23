from django.core.management import BaseCommand
from recipe.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        tags = [
            {'name': 'Еда', 'color': '#49B64E', 'slug': 'food'},
            {'name': 'Не еда', 'color': '#000000', 'slug': 'notfood'},
            {'name': 'Шедевр!', 'color': '#FF0000', 'slug': 'masterpiece'}
        ]
        Tag.objects.bulk_create(Tag(**tag) for tag in tags)
        self.stdout.write(self.style.SUCCESS('SUCCESS'))
