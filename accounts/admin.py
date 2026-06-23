from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Client, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Show and edit the role field inside Django admin."""

    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')

    # Add the role field to the existing edit + create forms.
    fieldsets = UserAdmin.fieldsets + (
        ('HVCS role', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('HVCS role', {'fields': ('role',)}),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('first_name', 'last_name', 'phone', 'email')
