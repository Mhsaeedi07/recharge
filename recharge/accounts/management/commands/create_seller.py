from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Seller
from rest_framework.authtoken.models import Token

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a seller user with a specific username and password'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='seller', help='Username for the seller')
        parser.add_argument('--password', type=str, default='74107410', help='Password for the seller')
        parser.add_argument('--credit', type=int, default=0, help='Initial credit amount')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        initial_credit = options['credit']


        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User with username "{username}" already exists'))
            user = User.objects.get(username=username)
        else:

            user = User.objects.create_user(
                username=username,
                password=password,
                is_seller=True
            )
            self.stdout.write(self.style.SUCCESS(f'User "{username}" created successfully'))


        if hasattr(user, 'seller_profile'):
            self.stdout.write(self.style.WARNING(f'Seller profile for "{username}" already exists'))
            seller = user.seller_profile
            seller.credit = initial_credit
            seller.save()
            self.stdout.write(self.style.SUCCESS(f'Seller profile updated with credit: {initial_credit}'))
        else:
            seller = Seller.objects.create(
                user=user,
                credit=initial_credit
            )
            self.stdout.write(self.style.SUCCESS(f'Seller profile created with credit: {initial_credit}'))

        token, created = Token.objects.get_or_create(user=user)
        if created:
            self.stdout.write(self.style.SUCCESS(f'API token created: {token.key}'))
        else:
            self.stdout.write(self.style.WARNING(f'Existing API token: {token.key}'))

        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('Seller account setup complete!'))
        self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'Token: {token.key}'))
        self.stdout.write(self.style.SUCCESS('='*50))