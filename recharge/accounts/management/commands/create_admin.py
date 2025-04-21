from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates an admin user with a specific username and password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Username for the admin')
        parser.add_argument('--password', type=str, default='85208520', help='Password for the admin')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User with username "{username}" already exists'))
            user = User.objects.get(username=username)
            # Update user to ensure they have admin privileges
            user.is_staff = True
            user.is_superuser = True
            user.is_admin_user = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User "{username}" updated with admin privileges'))
        else:
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                is_staff=True,
                is_superuser=True,
                is_admin_user=True
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" created successfully'))

        # Create token for API access
        token, created = Token.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS(f'API token created: {token.key}'))
        else:
            self.stdout.write(self.style.WARNING(f'Existing API token: {token.key}'))

        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Admin account setup complete!'))
        self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'Token: {token.key}'))
        self.stdout.write(self.style.SUCCESS('='*50))