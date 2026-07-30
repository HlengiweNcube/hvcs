from django.contrib import admin
from .models import Caregiver, Client, User, Visit


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_active')
    list_filter = ('role',)
    search_fields = ('username', 'email')


@admin.register(Caregiver)
class CaregiverAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'user', 'phone', 'is_active')
    list_select_related = ('user',)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'contact_phone', 'is_active')


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'caregiver', 'client', 'scheduled_date', 'scheduled_time', 'status')
    list_filter = ('status',)
    list_select_related = ('caregiver', 'client')

