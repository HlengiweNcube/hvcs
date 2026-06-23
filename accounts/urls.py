from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='accounts_home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('caregiver-dashboard/', views.caregiver_dashboard, name='caregiver_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('caregivers/', views.caregiver_list, name='caregiver_list'),
    path('caregivers/add/', views.caregiver_create, name='caregiver_create'),
    path('caregivers/<int:pk>/edit/', views.caregiver_update, name='caregiver_update'),
    path('caregivers/<int:pk>/delete/', views.caregiver_delete, name='caregiver_delete'),
]
