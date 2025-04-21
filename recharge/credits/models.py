from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from accounts.models import Seller


class CreditRequest(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    reference_id = models.CharField(
        max_length=255,
        unique=True
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name="credit_requests"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    processed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "credit_requests"
        indexes = [
            models.Index(fields=['seller']),
            models.Index(fields=['status']),
            models.Index(fields=['reference_id']),
        ]

    def __str__(self):
        return f"{self.seller} - {self.amount} - {self.get_status_display()}"


class Transaction(models.Model):

    TRANSACTION_TYPE_CHOICES = [
        ('credit_increase', 'Credit Increase'),
        ('charge_sale', 'Charge Sale'),
    ]

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    idempotency_key = models.CharField(
        max_length=255,
        unique=True
    )
    seller = models.ForeignKey(
        Seller,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    object_id = models.PositiveIntegerField(
        blank=True,
        null=True
    )
    related_to = GenericForeignKey('content_type', 'object_id')
    previous_credit = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    new_credit = models.DecimalField(
        max_digits=12,
        decimal_places=0
    )
    description = models.TextField(
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='processing'
    )
    created_at = models.DateTimeField(
        default=timezone.now
    )
    completed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        db_table = "transactions"
        indexes = [
            models.Index(fields=['seller']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.seller} - {self.amount} - {self.get_transaction_type_display()}"