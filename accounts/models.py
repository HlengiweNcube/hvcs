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

