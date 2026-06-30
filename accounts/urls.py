from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.landing, name='accounts_home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('caregiver-dashboard/', views.caregiver_dashboard, name='caregiver_dashboard'),
    path('caregiver-dashboard/profile/', views.caregiver_my_profile, name='caregiver_my_profile'),
    path('caregiver-dashboard/visits/', views.caregiver_my_visits, name='caregiver_my_visits'),
    path('caregiver-dashboard/visits/<int:pk>/', views.caregiver_visit_detail, name='caregiver_visit_detail'),
    path('caregiver-dashboard/visits/<int:pk>/checkin/', views.caregiver_checkin, name='caregiver_checkin'),
    path('caregiver-dashboard/visits/<int:pk>/checkout/', views.caregiver_checkout, name='caregiver_checkout'),
    path('caregiver-dashboard/clients/', views.caregiver_my_clients, name='caregiver_my_clients'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/add/', views.client_create, name='client_create'),
    path('clients/<int:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('caregivers/', views.caregiver_list, name='caregiver_list'),
    path('caregivers/add/', views.caregiver_create, name='caregiver_create'),
    path('caregivers/<int:pk>/edit/', views.caregiver_update, name='caregiver_update'),
    path('caregivers/<int:pk>/delete/', views.caregiver_delete, name='caregiver_delete'),
    path('visits/', views.visit_list, name='visit_list'),
    path('visits/add/', views.visit_create, name='visit_create'),
    path('visits/<int:pk>/edit/', views.visit_update, name='visit_update'),
    path('visits/<int:pk>/delete/', views.visit_delete, name='visit_delete'),
    path('managers/', views.manager_list, name='manager_list'),
    path('managers/add/', views.manager_create, name='manager_create'),
    path('managers/<int:pk>/edit/', views.manager_update, name='manager_update'),
    path('managers/<int:pk>/delete/', views.manager_delete, name='manager_delete'),
]
