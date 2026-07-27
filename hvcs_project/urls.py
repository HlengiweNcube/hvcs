
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.http import HttpResponse
from pathlib import Path

from accounts import views as account_views

BASE_DIR = Path(__file__).resolve().parent.parent

def react_spa(request, path=''):
    """Serve the Vite-built React SPA for any /react/* URL."""
    index = BASE_DIR / 'frontend' / 'dist' / 'index.html'
    if index.exists():
        return HttpResponse(index.read_text(encoding='utf-8'), content_type='text/html; charset=utf-8')
    return HttpResponse(
        'React app not built. Run: cd frontend && npm run build',
        status=503,
    )

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

    # React SPA — catch all /react/* paths and return the built index.html
    re_path(r'^react/.*$', react_spa),
]
