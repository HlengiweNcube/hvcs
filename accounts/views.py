from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import role_required
from .models import Client, User


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('first_name', 'last_name', 'phone', 'email', 'address', 'is_active')


class CaregiverCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CAREGIVER
        if commit:
            user.save()
        return user


class CaregiverUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')


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


@role_required(User.Role.ADMIN)
def client_list(request):
    clients = Client.objects.all()
    return render(request, 'accounts/client_list.html', {'clients': clients})


@role_required(User.Role.ADMIN)
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm()
    return render(request, 'accounts/client_form.html', {'form': form, 'title': 'Add Client'})


@role_required(User.Role.ADMIN)
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    return render(request, 'accounts/client_form.html', {'form': form, 'title': 'Edit Client'})


@role_required(User.Role.ADMIN)
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        return redirect('client_list')
    return render(request, 'accounts/client_confirm_delete.html', {'client': client})


@role_required(User.Role.ADMIN)
def caregiver_list(request):
    caregivers = User.objects.filter(role=User.Role.CAREGIVER).order_by('username')
    return render(request, 'accounts/caregiver_list.html', {'caregivers': caregivers})


@role_required(User.Role.ADMIN)
def caregiver_create(request):
    if request.method == 'POST':
        form = CaregiverCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('caregiver_list')
    else:
        form = CaregiverCreateForm()
    return render(request, 'accounts/caregiver_form.html', {'form': form, 'title': 'Add Caregiver'})


@role_required(User.Role.ADMIN)
def caregiver_update(request, pk):
    caregiver = get_object_or_404(User, pk=pk, role=User.Role.CAREGIVER)
    if request.method == 'POST':
        form = CaregiverUpdateForm(request.POST, instance=caregiver)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.role = User.Role.CAREGIVER
            updated.save()
            return redirect('caregiver_list')
    else:
        form = CaregiverUpdateForm(instance=caregiver)
    return render(request, 'accounts/caregiver_form.html', {'form': form, 'title': 'Edit Caregiver'})


@role_required(User.Role.ADMIN)
def caregiver_delete(request, pk):
    caregiver = get_object_or_404(User, pk=pk, role=User.Role.CAREGIVER)
    if request.method == 'POST':
        caregiver.delete()
        return redirect('caregiver_list')
    return render(request, 'accounts/caregiver_confirm_delete.html', {'caregiver': caregiver})

