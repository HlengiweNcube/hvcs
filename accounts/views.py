from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import role_required
from .models import Caregiver, Client, User


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ('first_name', 'last_name', 'address', 'contact_phone', 'care_needs', 'is_active')


class CaregiverCreateForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    phone = forms.CharField(max_length=30, required=False)
    qualifications = forms.CharField(max_length=255, required=False)
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CAREGIVER
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = self.cleaned_data['is_active']
        if commit:
            user.save()
            Caregiver.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                qualifications=self.cleaned_data['qualifications'],
                is_active=self.cleaned_data['is_active'],
            )
        return user


class CaregiverUpdateForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)

    class Meta:
        model = Caregiver
        fields = ('first_name', 'last_name', 'phone', 'qualifications', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        caregiver = super().save(commit=False)
        caregiver.user.username = self.cleaned_data['username']
        caregiver.user.email = self.cleaned_data['email']
        caregiver.user.first_name = self.cleaned_data['first_name']
        caregiver.user.last_name = self.cleaned_data['last_name']
        caregiver.user.is_active = self.cleaned_data['is_active']
        caregiver.user.role = User.Role.CAREGIVER
        if commit:
            caregiver.user.save()
            caregiver.save()
        return caregiver


def landing(request):
    """HVCS landing page."""
    return render(request, 'accounts/landing.html')


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
    caregivers = Caregiver.objects.select_related('user').all()
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
    caregiver = get_object_or_404(Caregiver, pk=pk, user__role=User.Role.CAREGIVER)
    if request.method == 'POST':
        form = CaregiverUpdateForm(request.POST, instance=caregiver)
        if form.is_valid():
            form.save()
            return redirect('caregiver_list')
    else:
        form = CaregiverUpdateForm(instance=caregiver)
    return render(request, 'accounts/caregiver_form.html', {'form': form, 'title': 'Edit Caregiver'})


@role_required(User.Role.ADMIN)
def caregiver_delete(request, pk):
    caregiver = get_object_or_404(Caregiver, pk=pk, user__role=User.Role.CAREGIVER)
    if request.method == 'POST':
        caregiver.user.delete()
        return redirect('caregiver_list')
    return render(request, 'accounts/caregiver_confirm_delete.html', {'caregiver': caregiver})

