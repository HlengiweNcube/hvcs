from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('caregiver-dashboard/', views.caregiver_dashboard, name='caregiver_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
]
