from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import role_required
from .models import User


@login_required
def dashboard(request):
    """Send each logged-in user to the dashboard for their role."""
    role = request.user.role
    if role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    if role == User.Role.MANAGER:
        return redirect('manager_dashboard')
    return redirect('caregiver_dashboard')


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html')


@role_required(User.Role.CAREGIVER)
def caregiver_dashboard(request):
    return render(request, 'accounts/caregiver_dashboard.html')


@role_required(User.Role.MANAGER)
def manager_dashboard(request):
    return render(request, 'accounts/manager_dashboard.html')

