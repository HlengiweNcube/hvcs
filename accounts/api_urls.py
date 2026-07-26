"""
API URL configuration — /api/v1/

All routes are JWT-protected (except login and register).
These are consumed exclusively by the React frontend.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import api_views

urlpatterns = [
    # Auth
    path('auth/login/',    api_views.LoginView.as_view(),  name='api_login'),
    path('auth/refresh/',  TokenRefreshView.as_view(),     name='api_token_refresh'),
    path('auth/register/', api_views.register_view,        name='api_register'),
    path('auth/me/',       api_views.me_view,              name='api_me'),

    # Dashboards
    path('dashboard/admin/',     api_views.admin_dashboard_view,    name='api_admin_dashboard'),
    path('dashboard/manager/',   api_views.manager_dashboard_view,  name='api_manager_dashboard'),
    path('dashboard/caregiver/', api_views.caregiver_dashboard_view, name='api_caregiver_dashboard'),

    # Clients
    path('clients/',      api_views.ClientListCreateView.as_view(), name='api_client_list'),
    path('clients/<int:pk>/', api_views.ClientDetailView.as_view(), name='api_client_detail'),

    # Caregivers
    path('caregivers/',       api_views.CaregiverListCreateView.as_view(), name='api_caregiver_list'),
    path('caregivers/<int:pk>/', api_views.CaregiverDetailView.as_view(),  name='api_caregiver_detail'),

    # Visits
    path('visits/',         api_views.VisitListCreateView.as_view(), name='api_visit_list'),
    path('visits/<int:pk>/', api_views.VisitDetailView.as_view(),   name='api_visit_detail'),
    path('visits/<int:pk>/checkin/',  api_views.visit_checkin,       name='api_visit_checkin'),
    path('visits/<int:pk>/checkout/', api_views.visit_checkout,      name='api_visit_checkout'),

    # Managers
    path('managers/',         api_views.ManagerListCreateView.as_view(), name='api_manager_list'),
    path('managers/<int:pk>/', api_views.ManagerDetailView.as_view(),    name='api_manager_detail'),

    # Compliance
    path('compliance/', api_views.compliance_view, name='api_compliance'),
]
