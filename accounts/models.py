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


class Caregiver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='caregiver_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    qualifications = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Client(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=30, blank=True)
    care_needs = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

