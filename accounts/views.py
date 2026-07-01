from django import forms
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import role_required
from .models import Caregiver, Client, User, Visit


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


def custom_logout(request):
    logout(request)
    return redirect('login')


class SelfRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField(required=False)
    phone = forms.CharField(max_length=30, required=False)
    qualifications = forms.CharField(max_length=255, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CAREGIVER
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.is_active = True
        if commit:
            user.save()
            Caregiver.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                qualifications=self.cleaned_data['qualifications'],
                is_active=True,
            )
        return user


def register(request):
    if request.user.is_authenticated:
        return redirect('accounts_home')
    if request.method == 'POST':
        form = SelfRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('caregiver_dashboard')
    else:
        form = SelfRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


class ManagerCreateForm(UserCreationForm):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.MANAGER
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ManagerUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active')


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
    today = timezone.now().date()
    now = timezone.now()
    week_ago = today - timezone.timedelta(days=7)

    # --- Alerts -------------------------------------------------------
    # 1. Missed check-in: scheduled today, time passed 15+ min, still SCHEDULED
    cutoff = now - timezone.timedelta(minutes=15)
    missed_checkin = (
        Visit.objects.filter(
            scheduled_date=today,
            status=Visit.Status.SCHEDULED,
        )
        .select_related('caregiver', 'client')
        .order_by('scheduled_time')
    )
    missed_checkin = [
        v for v in missed_checkin
        if timezone.make_aware(
            timezone.datetime.combine(today, v.scheduled_time)
        ) <= cutoff
    ]

    # 2. Never-started: scheduled_date < today and still SCHEDULED
    never_started = (
        Visit.objects.filter(
            scheduled_date__lt=today,
            status=Visit.Status.SCHEDULED,
        )
        .select_related('caregiver', 'client')
        .order_by('-scheduled_date')
    )
    alerts = {
        'missed_checkin': missed_checkin,
        'never_started': never_started,
    }
    # ------------------------------------------------------------------

    stats = {
        'total_clients': Client.objects.filter(is_active=True).count(),
        'total_caregivers': Caregiver.objects.filter(is_active=True).count(),
        'total_managers': User.objects.filter(role=User.Role.MANAGER).count(),
        'visits_scheduled': Visit.objects.filter(status=Visit.Status.SCHEDULED).count(),
        'visits_in_progress': Visit.objects.filter(status=Visit.Status.IN_PROGRESS).count(),
        'visits_completed': Visit.objects.filter(status=Visit.Status.COMPLETED).count(),
        'visits_cancelled': Visit.objects.filter(status=Visit.Status.CANCELLED).count(),
    }

    # Compliance rate: completed / (completed + cancelled) over last 7 days
    recent_done = Visit.objects.filter(
        scheduled_date__gte=week_ago,
        status__in=[Visit.Status.COMPLETED, Visit.Status.CANCELLED],
    ).count()
    recent_completed = Visit.objects.filter(
        scheduled_date__gte=week_ago,
        status=Visit.Status.COMPLETED,
    ).count()
    compliance_rate = round((recent_completed / recent_done * 100) if recent_done else 0)

    todays_visits = (
        Visit.objects.filter(scheduled_date=today)
        .select_related('caregiver', 'client')
        .order_by('scheduled_time')
    )
    recent_visits = (
        Visit.objects.filter(scheduled_date__gte=week_ago, scheduled_date__lt=today)
        .select_related('caregiver', 'client')
        .order_by('-scheduled_date', 'scheduled_time')
    )

    return render(request, 'accounts/admin_dashboard.html', {
        'stats': stats,
        'todays_visits': todays_visits,
        'recent_visits': recent_visits,
        'compliance_rate': compliance_rate,
        'alerts': alerts,
    })


@role_required(User.Role.CAREGIVER)
def caregiver_dashboard(request):
    caregiver = get_object_or_404(Caregiver, user=request.user)
    clients = Client.objects.filter(is_active=True)
    visits = Visit.objects.filter(caregiver=caregiver).select_related('client')
    return render(request, 'accounts/caregiver_dashboard.html', {
        'caregiver': caregiver,
        'clients': clients,
        'visits': visits,
    })


@role_required(User.Role.CAREGIVER)
def caregiver_my_profile(request):
    caregiver = get_object_or_404(Caregiver, user=request.user)
    return render(request, 'accounts/caregiver_profile.html', {'caregiver': caregiver})


@role_required(User.Role.CAREGIVER)
def caregiver_my_visits(request):
    caregiver = get_object_or_404(Caregiver, user=request.user)
    visits = Visit.objects.filter(caregiver=caregiver).select_related('client')
    return render(request, 'accounts/caregiver_visits.html', {'caregiver': caregiver, 'visits': visits})


@role_required(User.Role.CAREGIVER)
def caregiver_my_clients(request):
    caregiver = get_object_or_404(Caregiver, user=request.user)
    client_ids = Visit.objects.filter(caregiver=caregiver).values_list('client_id', flat=True).distinct()
    clients = Client.objects.filter(id__in=client_ids, is_active=True)
    return render(request, 'accounts/caregiver_clients.html', {'caregiver': caregiver, 'clients': clients})


@role_required(User.Role.CAREGIVER)
def caregiver_visit_detail(request, pk):
    caregiver = get_object_or_404(Caregiver, user=request.user)
    visit = get_object_or_404(Visit, pk=pk, caregiver=caregiver)
    if request.method == 'POST':
        form = VisitNotesForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('caregiver_visit_detail', pk=pk)
    else:
        form = VisitNotesForm(instance=visit)
    return render(request, 'accounts/caregiver_visit_detail.html', {'visit': visit, 'form': form})


@role_required(User.Role.CAREGIVER)
def caregiver_checkin(request, pk):
    if request.method == 'POST':
        caregiver = get_object_or_404(Caregiver, user=request.user)
        visit = get_object_or_404(Visit, pk=pk, caregiver=caregiver)
        if visit.status == Visit.Status.SCHEDULED:
            try:
                lat = request.POST.get('lat', '').strip()
                lng = request.POST.get('lng', '').strip()
                visit.check_in_lat = lat if lat else None
                visit.check_in_lng = lng if lng else None
                visit.check_in_time = timezone.now()
                visit.status = Visit.Status.IN_PROGRESS
                visit.save()
            except Exception:
                pass
    return redirect('caregiver_visit_detail', pk=pk)


@role_required(User.Role.CAREGIVER)
def caregiver_checkout(request, pk):
    if request.method == 'POST':
        caregiver = get_object_or_404(Caregiver, user=request.user)
        visit = get_object_or_404(Visit, pk=pk, caregiver=caregiver)
        if visit.status == Visit.Status.IN_PROGRESS:
            visit.check_out_time = timezone.now()
            visit.status = Visit.Status.COMPLETED
            visit.save()
    return redirect('caregiver_visit_detail', pk=pk)


@role_required(User.Role.MANAGER)
def manager_dashboard(request):
    today = timezone.now().date()
    now = timezone.now()
    cutoff = now - timezone.timedelta(minutes=15)

    missed_checkin = (
        Visit.objects.filter(
            scheduled_date=today,
            status=Visit.Status.SCHEDULED,
        )
        .select_related('caregiver', 'client')
        .order_by('scheduled_time')
    )
    missed_checkin = [
        v for v in missed_checkin
        if timezone.make_aware(
            timezone.datetime.combine(today, v.scheduled_time)
        ) <= cutoff
    ]

    never_started = (
        Visit.objects.filter(
            scheduled_date__lt=today,
            status=Visit.Status.SCHEDULED,
        )
        .select_related('caregiver', 'client')
        .order_by('-scheduled_date')
    )

    todays_visits = (
        Visit.objects.filter(scheduled_date=today)
        .select_related('caregiver', 'client')
        .order_by('scheduled_time')
    )

    alerts = {
        'missed_checkin': missed_checkin,
        'never_started': never_started,
    }
    return render(request, 'accounts/manager_dashboard.html', {
        'alerts': alerts,
        'todays_visits': todays_visits,
    })


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


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ('caregiver', 'client', 'scheduled_date', 'scheduled_time', 'status', 'notes')
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class VisitNotesForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ('notes',)
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }


@role_required(User.Role.ADMIN)
def visit_list(request):
    visits = Visit.objects.select_related('caregiver', 'client').all()

    # Optional filters
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if date_from:
        visits = visits.filter(scheduled_date__gte=date_from)
    if date_to:
        visits = visits.filter(scheduled_date__lte=date_to)
    if status_filter:
        visits = visits.filter(status=status_filter)

    return render(request, 'accounts/visit_list.html', {
        'visits': visits,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
        'status_choices': Visit.Status.choices,
    })


@role_required(User.Role.ADMIN)
def visit_create(request):
    if request.method == 'POST':
        form = VisitForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('visit_list')
    else:
        form = VisitForm()
    return render(request, 'accounts/visit_form.html', {'form': form, 'title': 'Schedule Visit'})


@role_required(User.Role.ADMIN)
def visit_update(request, pk):
    visit = get_object_or_404(Visit, pk=pk)
    if request.method == 'POST':
        form = VisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            return redirect('visit_list')
    else:
        form = VisitForm(instance=visit)
    return render(request, 'accounts/visit_form.html', {'form': form, 'title': 'Edit Visit'})


@role_required(User.Role.ADMIN)
def visit_delete(request, pk):
    visit = get_object_or_404(Visit, pk=pk)
    if request.method == 'POST':
        visit.delete()
        return redirect('visit_list')
    return render(request, 'accounts/visit_confirm_delete.html', {'visit': visit})


@role_required(User.Role.ADMIN)
def manager_list(request):
    managers = User.objects.filter(role=User.Role.MANAGER)
    return render(request, 'accounts/manager_list.html', {'managers': managers})


@role_required(User.Role.ADMIN)
def manager_create(request):
    if request.method == 'POST':
        form = ManagerCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manager_list')
    else:
        form = ManagerCreateForm()
    return render(request, 'accounts/manager_form.html', {'form': form, 'title': 'Add Manager'})


@role_required(User.Role.ADMIN)
def manager_update(request, pk):
    manager = get_object_or_404(User, pk=pk, role=User.Role.MANAGER)
    if request.method == 'POST':
        form = ManagerUpdateForm(request.POST, instance=manager)
        if form.is_valid():
            form.save()
            return redirect('manager_list')
    else:
        form = ManagerUpdateForm(instance=manager)
    return render(request, 'accounts/manager_form.html', {'form': form, 'title': 'Edit Manager'})


@role_required(User.Role.ADMIN)
def manager_delete(request, pk):
    manager = get_object_or_404(User, pk=pk, role=User.Role.MANAGER)
    if request.method == 'POST':
        manager.delete()
        return redirect('manager_list')
    return render(request, 'accounts/manager_confirm_delete.html', {'manager': manager})


