
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts import views as account_views

urlpatterns = [
    # Legacy Django-template views (unchanged)
    path('accounts/', include('accounts.urls')),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='home'),

    # REST API consumed by React frontend
    path('api/v1/', include('accounts.api_urls')),
]
