from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@email.com', 'admin123')
            self.stdout.write('Superuser created.')
        else:
            self.stdout.write('Superuser already exists.')