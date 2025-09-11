from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Create a superuser for the custom User model (email as username)'

    def handle(self, *args, **options):
        email = input('Email: ').strip()
        name = input('Name: ').strip()
        password = input('Password: ').strip()

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR('A user with this email already exists.'))
            return

        user = User(email=email, name=name, is_staff=True, is_superuser=True)
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'Superuser created successfully: {user.email}'))
