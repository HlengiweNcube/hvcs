from django.contrib import admin
from .models import Caregiver, Client, User, Visit


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'created_by', 'is_active')
    list_filter = ('role',)
    list_select_related = ('created_by',)
    search_fields = ('username', 'email')


@admin.register(Caregiver)
class CaregiverAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'user', 'supervised_by', 'phone', 'employment_status', 'date_left', 'is_active')
    list_filter = ('employment_status', 'is_active')
    list_select_related = ('user', 'supervised_by')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'assigned_caregiver', 'contact_phone', 'is_active')
    list_select_related = ('assigned_caregiver',)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'caregiver', 'client', 'scheduled_date', 'scheduled_time', 'status')
    list_filter = ('status',)
    list_select_related = ('caregiver', 'client')

