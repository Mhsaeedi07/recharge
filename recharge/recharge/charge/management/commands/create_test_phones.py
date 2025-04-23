from django.core.management.base import BaseCommand
from charge.models import PhoneNumber

class Command(BaseCommand):
    help = 'Creates test phone numbers for development and testing'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of phone numbers to create')
        parser.add_argument('--prefix', type=str, default='0912', help='Phone number prefix')

    def handle(self, *args, **options):
        count = options['count']
        prefix = options['prefix']

        created = 0
        for i in range(1, count + 1):
            number = f"{prefix}{i:07d}"

            if not PhoneNumber.objects.filter(number=number).exists():
                PhoneNumber.objects.create(
                    number=number,
                    current_balance=0
                )
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created phone number: {number}'))
            else:
                self.stdout.write(self.style.WARNING(f'Phone number already exists: {number}'))

        self.stdout.write(self.style.SUCCESS(f'Created {created} new phone numbers'))