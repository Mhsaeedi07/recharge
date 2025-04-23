from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):

    is_seller = models.BooleanField(default=False)
    is_admin_user = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='user permissions',
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.get_full_name() or self.username


class Seller(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="seller_profile"
    )
    credit = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0
    )

    created_at = models.DateTimeField(
        default=timezone.now
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        db_table = "sellers"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.credit}"