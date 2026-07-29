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
    """
    Profile record for a caregiver user.

    Linked 1-to-1 to a User via a OneToOneField so that Django's auth
    system handles credentials while this model stores care-specific data.
    Deleting the User cascades and removes this profile automatically.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='caregiver_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    qualifications = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='caregiver_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('last_name', 'first_name')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Client(models.Model):
    """
    A client who receives home care visits.

    Clients are not Users — they do not log in.  Care needs are stored as
    free text so that the system remains flexible across care types.
    """
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


class Visit(models.Model):
    """
    A scheduled home care visit between a Caregiver and a Client.

    Status transitions:
      SCHEDULED → IN_PROGRESS (caregiver checks in)
      IN_PROGRESS → COMPLETED  (caregiver checks out)
      SCHEDULED / IN_PROGRESS → CANCELLED (admin cancels)

    GPS coordinates (check_in_lat/lng) are optional — caregivers can check
    in without location permission.  check_in_address is populated by the
    reverse_geocode() helper after a successful GPS check-in.
    """

    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    caregiver = models.ForeignKey(Caregiver, on_delete=models.CASCADE, related_name='visits')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='visits')
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.TextField(blank=True)
    check_in_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    check_in_address = models.CharField(max_length=255, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('scheduled_date', 'scheduled_time')

    def __str__(self):
        return f'{self.scheduled_date} {self.scheduled_time} — {self.caregiver} → {self.client}'

