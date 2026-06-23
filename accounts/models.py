from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role that drives which dashboard they see."""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        CAREGIVER = 'CAREGIVER', 'Caregiver'
        MANAGER = 'MANAGER', 'Manager'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CAREGIVER,
        help_text='Determines what this user can see and do.',
    )

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'


class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

