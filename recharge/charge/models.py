from django.db import models
from django.utils import timezone

from accounts.models import Seller


class PhoneNumber(models.Model):

    number = models.CharField(
        max_length=20,
        unique=True
    )
    current_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )
    last_charge_date = models.DateTimeField(
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "phone_numbers"
        indexes = [
            models.Index(fields=['number']),
        ]

    def __str__(self):
        return f"{self.number} - Balance: {self.current_balance}"


class ChargeSale(models.Model):

    STATUS_CHOICES = [
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    transaction_uuid = models.CharField(
        max_length=255,
        unique=True
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name="charge_sales"
    )
    phone_number = models.ForeignKey(
        PhoneNumber,
        on_delete=models.CASCADE,
        related_name="charges"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    phone_initial_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    phone_final_balance = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='successful'
    )
    status_message = models.TextField(
        blank=True
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "charge_sales"
        indexes = [
            models.Index(fields=['seller']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_uuid']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.seller} - {self.phone_number} - {self.amount}"