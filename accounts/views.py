import csv
import json
import urllib.request

from django import forms
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import role_required
from .models import Caregiver, Client, User, Visit


def reverse_geocode(lat, lng):
    """Return a human-readable address for the given coordinates using the
    free OpenStreetMap Nominatim API (no API key required).
    Returns an empty string if the call fails for any reason.
    """
    url = (
        f"https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lng}&format=json"
    )
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'HVCS/1.0 (home-visit-care-system)'},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get('display_name', '')
    except Exception:
        return ''


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

    # Compliance rate: completed / all non-cancelled past visits (last 7 days)
    # Missed visits (still SCHEDULED, date in past) count against the rate.
    recent_completed = Visit.objects.filter(
        scheduled_date__gte=week_ago,
        scheduled_date__lte=today,
        status=Visit.Status.COMPLETED,
    ).count()
    recent_denominator = Visit.objects.filter(
        scheduled_date__gte=week_ago,
        scheduled_date__lte=today,
    ).exclude(status=Visit.Status.CANCELLED).count()
    compliance_rate = round((recent_completed / recent_denominator * 100) if recent_denominator else 0)

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
            messages.success(request, 'Notes saved successfully.')
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
                if lat and lng:
                    visit.check_in_address = reverse_geocode(lat, lng)
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
    week_ago = today - timezone.timedelta(days=7)

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

    caregivers = Caregiver.objects.filter(is_active=True).select_related('user').order_by('last_name', 'first_name')

    # --- Per-caregiver compliance (last 7 days) ----------------------------
    caregiver_compliance = []
    for cg in caregivers:
        qs = Visit.objects.filter(
            caregiver=cg,
            scheduled_date__gte=week_ago,
            scheduled_date__lte=today,
        ).exclude(status=Visit.Status.CANCELLED)
        total = qs.count()
        completed = qs.filter(status=Visit.Status.COMPLETED).count()
        rate = round(completed / total * 100) if total else None
        caregiver_compliance.append({
            'caregiver': cg,
            'total': total,
            'completed': completed,
            'rate': rate,
        })
    # -----------------------------------------------------------------------

    missing_notes = list(
        Visit.objects.filter(
            status=Visit.Status.COMPLETED,
            notes='',
        )
        .select_related('caregiver', 'client')
        .order_by('-scheduled_date')[:20]
    )

    alerts = {
        'missed_checkin': missed_checkin,
        'never_started': never_started,
        'missing_notes': missing_notes,
    }
    return render(request, 'accounts/manager_dashboard.html', {
        'alerts': alerts,
        'todays_visits': todays_visits,
        'caregivers': caregivers,
        'caregiver_compliance': caregiver_compliance,
    })


@role_required(User.Role.ADMIN, User.Role.MANAGER)
def compliance_dashboard(request):
    today = timezone.now().date()

    # Default date range: last 30 days
    default_from = today - timezone.timedelta(days=30)
    date_from_str = request.GET.get('date_from', str(default_from))
    date_to_str = request.GET.get('date_to', str(today))

    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
    except ValueError:
        date_from = default_from
    try:
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except ValueError:
        date_to = today

    visits_qs = Visit.objects.filter(
        scheduled_date__gte=date_from,
        scheduled_date__lte=date_to,
    ).select_related('caregiver', 'client')

    # Per-caregiver breakdown
    caregiver_stats = []
    for caregiver in Caregiver.objects.filter(is_active=True).select_related('user').order_by('last_name', 'first_name'):
        cv = visits_qs.filter(caregiver=caregiver)
        assigned   = cv.count()
        completed  = cv.filter(status=Visit.Status.COMPLETED).count()
        cancelled  = cv.filter(status=Visit.Status.CANCELLED).count()
        missed     = cv.filter(status=Visit.Status.SCHEDULED, scheduled_date__lt=today).count()
        in_progress = cv.filter(status=Visit.Status.IN_PROGRESS).count()

        # Late check-in: check_in_time more than 15 min after scheduled
        late = 0
        for v in cv.filter(check_in_time__isnull=False):
            expected = timezone.make_aware(
                timezone.datetime.combine(v.scheduled_date, v.scheduled_time)
            )
            if v.check_in_time > expected + timezone.timedelta(minutes=15):
                late += 1

        no_notes = cv.filter(status=Visit.Status.COMPLETED, notes='').count()
        # Exclude cancelled — not the caregiver's fault. N/A if nothing to measure.
        expected_to_complete = assigned - cancelled
        rate = round(completed / expected_to_complete * 100) if expected_to_complete > 0 else None

        caregiver_stats.append({
            'caregiver': caregiver,
            'assigned': assigned,
            'completed': completed,
            'cancelled': cancelled,
            'missed': missed,
            'in_progress': in_progress,
            'late': late,
            'no_notes': no_notes,
            'rate': rate,
        })

    # Overall summary
    total_assigned  = visits_qs.count()
    total_completed = visits_qs.filter(status=Visit.Status.COMPLETED).count()
    total_cancelled = visits_qs.filter(status=Visit.Status.CANCELLED).count()
    total_missed    = visits_qs.filter(status=Visit.Status.SCHEDULED, scheduled_date__lt=today).count()
    total_closed    = total_assigned - total_cancelled
    overall_rate    = round(total_completed / total_closed * 100) if total_closed > 0 else None

    return render(request, 'accounts/compliance_dashboard.html', {
        'caregiver_stats': caregiver_stats,
        'date_from': date_from_str,
        'date_to': date_to_str,
        'summary': {
            'assigned': total_assigned,
            'completed': total_completed,
            'cancelled': total_cancelled,
            'missed': total_missed,
            'overall_rate': overall_rate,
        },
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


@role_required(User.Role.MANAGER)
def send_schedule_email(request):
    """Fallback: manager sends a caregiver's upcoming schedule by email."""
    if request.method != 'POST':
        return redirect('manager_dashboard')

    caregiver_id = request.POST.get('caregiver_id', '').strip()
    caregiver = get_object_or_404(Caregiver, pk=caregiver_id, is_active=True)

    email_address = caregiver.user.email
    if not email_address:
        messages.error(request, f'{caregiver} has no email address on record.')
        return redirect('manager_dashboard')

    today = timezone.now().date()
    upcoming = (
        Visit.objects.filter(
            caregiver=caregiver,
            scheduled_date__gte=today,
            status=Visit.Status.SCHEDULED,
        )
        .select_related('client')
        .order_by('scheduled_date', 'scheduled_time')
    )

    if not upcoming.exists():
        messages.warning(request, f'No upcoming scheduled visits found for {caregiver}.')
        return redirect('manager_dashboard')

    lines = [f'Hi {caregiver.first_name},\n']
    lines.append('Here is your upcoming visit schedule:\n')
    for v in upcoming:
        lines.append(f'  {v.scheduled_date}  {v.scheduled_time}  —  {v.client}')
    lines.append('\nPlease log in to the HVCS system to check in for each visit.')
    lines.append('If you have trouble logging in, contact your manager immediately.')

    send_mail(
        subject='Your HVCS Visit Schedule',
        message='\n'.join(lines),
        from_email=None,   # uses DEFAULT_FROM_EMAIL
        recipient_list=[email_address],
        fail_silently=False,
    )

    messages.success(request, f'Schedule emailed to {caregiver} ({email_address}).')
    return redirect('manager_dashboard')


@role_required(User.Role.ADMIN, User.Role.MANAGER)
def export_audit_report(request):
    """Download a CSV audit report of all visits for a given date range."""
    today = timezone.now().date()
    default_from = today - timezone.timedelta(days=30)

    date_from_str = request.GET.get('date_from', str(default_from))
    date_to_str = request.GET.get('date_to', str(today))

    try:
        date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
        date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
    except ValueError:
        date_from, date_to = default_from, today

    visits = (
        Visit.objects.filter(
            scheduled_date__gte=date_from,
            scheduled_date__lte=date_to,
        )
        .select_related('caregiver__user', 'client')
        .order_by('scheduled_date', 'scheduled_time')
    )

    filename = f'hvcs_audit_{date_from}_{date_to}.csv'
    from django.http import HttpResponse as _HR
    response = _HR(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Date', 'Time', 'Caregiver', 'Client',
        'Status', 'Check-in Time', 'Check-out Time',
        'GPS Address', 'Notes',
    ])
    for v in visits:
        writer.writerow([
            v.scheduled_date,
            v.scheduled_time,
            str(v.caregiver),
            str(v.client),
            v.get_status_display(),
            v.check_in_time.strftime('%Y-%m-%d %H:%M') if v.check_in_time else '',
            v.check_out_time.strftime('%Y-%m-%d %H:%M') if v.check_out_time else '',
            v.check_in_address,
            v.notes,
        ])

    return response
