
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
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
    path('admin/', admin.site.urls),
    # Legacy Django-template views (unchanged)
    path('accounts/', include('accounts.urls')),
    path('dashboard/', account_views.dashboard, name='dashboard'),
    path('', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='home'),

    # Password reset — four built-in Django views
    path('accounts/password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.txt',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/',
         ),
         name='password_reset'),
    path('accounts/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/accounts/reset/done/',
         ),
         name='password_reset_confirm'),
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    # REST API consumed by React frontend
    path('api/v1/', include('accounts.api_urls')),

    # React SPA — catch all /react/* paths and return the built index.html
    re_path(r'^react/.*$', react_spa),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
