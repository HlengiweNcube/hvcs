"""
HVCS REST API views.

All endpoints are JWT-authenticated.  Role enforcement mirrors the existing
decorator-based template views so both surfaces stay consistent.
Endpoints live under /api/v1/ — completely separate from the existing
Django-template URLs, so nothing in the current app is broken.
"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Caregiver, Client, User, Visit
from .serializers import (
    CaregiverSerializer,
    CaregiverWriteSerializer,
    ClientSerializer,
    ManagerCreateSerializer,
    ManagerSerializer,
    RegisterSerializer,
    UserSerializer,
    VisitCheckinSerializer,
    VisitSerializer,
)


# ---------------------------------------------------------------------------
# Helper: role-based permission mixins
# ---------------------------------------------------------------------------

class AdminOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.ADMIN


class AdminOrManager(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.role in (User.Role.ADMIN, User.Role.MANAGER)
        )


class CaregiverOnly(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == User.Role.CAREGIVER


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginView(TokenObtainPairView):
    """
    POST /api/v1/auth/login/
    Returns access + refresh JWT tokens.
    The access token must be sent as  Authorization: Bearer <token>  on every
    subsequent request.
    """
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    POST /api/v1/auth/register/
    Self-registration for new caregivers.
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({'detail': 'Registration successful. Please log in.'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """
    GET /api/v1/auth/me/
    Returns the logged-in user's profile and role so React can decide
    which dashboard to render.
    """
    return Response(UserSerializer(request.user).data)


# ---------------------------------------------------------------------------
# Admin dashboard summary
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AdminOnly])
def admin_dashboard_view(request):
    """
    GET /api/v1/dashboard/admin/
    Aggregated stats consumed by the React admin dashboard.
    """
    today = timezone.now().date()
    now = timezone.now()
    week_ago = today - timezone.timedelta(days=7)
    cutoff = now - timezone.timedelta(minutes=15)

    missed_checkin_qs = Visit.objects.filter(
        scheduled_date=today, status=Visit.Status.SCHEDULED
    ).select_related('caregiver', 'client')
    missed_checkin = [
        v for v in missed_checkin_qs
        if timezone.make_aware(timezone.datetime.combine(today, v.scheduled_time)) <= cutoff
    ]
    never_started = list(
        Visit.objects.filter(scheduled_date__lt=today, status=Visit.Status.SCHEDULED)
        .select_related('caregiver', 'client')
        .order_by('-scheduled_date')
    )

    recent_completed = Visit.objects.filter(
        scheduled_date__gte=week_ago, scheduled_date__lte=today,
        status=Visit.Status.COMPLETED,
    ).count()
    recent_denom = Visit.objects.filter(
        scheduled_date__gte=week_ago, scheduled_date__lte=today,
    ).exclude(status=Visit.Status.CANCELLED).count()

    return Response({
        'stats': {
            'total_clients':    Client.objects.filter(is_active=True).count(),
            'total_caregivers': Caregiver.objects.filter(is_active=True).count(),
            'total_managers':   User.objects.filter(role=User.Role.MANAGER).count(),
            'visits_scheduled':   Visit.objects.filter(status=Visit.Status.SCHEDULED).count(),
            'visits_in_progress': Visit.objects.filter(status=Visit.Status.IN_PROGRESS).count(),
            'visits_completed':   Visit.objects.filter(status=Visit.Status.COMPLETED).count(),
            'visits_cancelled':   Visit.objects.filter(status=Visit.Status.CANCELLED).count(),
            'compliance_rate': round(recent_completed / recent_denom * 100) if recent_denom else 0,
        },
        'alerts': {
            'missed_checkin': VisitSerializer(missed_checkin, many=True).data,
            'never_started':  VisitSerializer(never_started,  many=True).data,
        },
        'todays_visits': VisitSerializer(
            Visit.objects.filter(scheduled_date=today)
            .select_related('caregiver', 'client').order_by('scheduled_time'),
            many=True,
        ).data,
    })


# ---------------------------------------------------------------------------
# Manager dashboard summary
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AdminOrManager])
def manager_dashboard_view(request):
    """GET /api/v1/dashboard/manager/"""
    today = timezone.now().date()
    now = timezone.now()
    cutoff = now - timezone.timedelta(minutes=15)

    missed_checkin_qs = Visit.objects.filter(
        scheduled_date=today, status=Visit.Status.SCHEDULED
    ).select_related('caregiver', 'client')
    missed_checkin = [
        v for v in missed_checkin_qs
        if timezone.make_aware(timezone.datetime.combine(today, v.scheduled_time)) <= cutoff
    ]
    never_started = list(
        Visit.objects.filter(scheduled_date__lt=today, status=Visit.Status.SCHEDULED)
        .select_related('caregiver', 'client').order_by('-scheduled_date')
    )

    return Response({
        'alerts': {
            'missed_checkin': VisitSerializer(missed_checkin, many=True).data,
            'never_started':  VisitSerializer(never_started,  many=True).data,
        },
        'todays_visits': VisitSerializer(
            Visit.objects.filter(scheduled_date=today)
            .select_related('caregiver', 'client').order_by('scheduled_time'),
            many=True,
        ).data,
        'caregivers': CaregiverSerializer(
            Caregiver.objects.filter(is_active=True).select_related('user'),
            many=True,
        ).data,
    })


# ---------------------------------------------------------------------------
# Caregiver dashboard
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([CaregiverOnly])
def caregiver_dashboard_view(request):
    """GET /api/v1/dashboard/caregiver/"""
    caregiver = Caregiver.objects.select_related('user').get(user=request.user)
    visits = Visit.objects.filter(caregiver=caregiver).select_related('client')
    return Response({
        'caregiver': CaregiverSerializer(caregiver).data,
        'visits': VisitSerializer(visits, many=True).data,
    })


# ---------------------------------------------------------------------------
# Clients CRUD  (Admin only)
# ---------------------------------------------------------------------------

class ClientListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/clients/   POST /api/v1/clients/"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [AdminOnly]


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/clients/<pk>/"""
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [AdminOnly]


# ---------------------------------------------------------------------------
# Caregivers CRUD  (Admin only)
# ---------------------------------------------------------------------------

class CaregiverListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/caregivers/   POST /api/v1/caregivers/"""
    queryset = Caregiver.objects.select_related('user').all()
    permission_classes = [AdminOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CaregiverWriteSerializer
        return CaregiverSerializer


class CaregiverDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/caregivers/<pk>/"""
    queryset = Caregiver.objects.select_related('user').all()
    permission_classes = [AdminOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CaregiverWriteSerializer
        return CaregiverSerializer

    def perform_destroy(self, instance):
        # Deleting the User cascades to the Caregiver row.
        instance.user.delete()


# ---------------------------------------------------------------------------
# Visits CRUD  (Admin manages all; caregiver sees own)
# ---------------------------------------------------------------------------

class VisitListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/visits/   POST /api/v1/visits/"""
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Visit.objects.select_related('caregiver', 'client')
        user = self.request.user
        if user.role == User.Role.CAREGIVER:
            caregiver = Caregiver.objects.get(user=user)
            qs = qs.filter(caregiver=caregiver)
        # Filtering
        date_from = self.request.query_params.get('date_from')
        date_to   = self.request.query_params.get('date_to')
        status_f  = self.request.query_params.get('status')
        if date_from:
            qs = qs.filter(scheduled_date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_date__lte=date_to)
        if status_f:
            qs = qs.filter(status=status_f)
        return qs

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AdminOnly()]
        return [IsAuthenticated()]


class VisitDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/visits/<pk>/"""
    serializer_class = VisitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Visit.objects.select_related('caregiver', 'client')
        user = self.request.user
        if user.role == User.Role.CAREGIVER:
            caregiver = Caregiver.objects.get(user=user)
            qs = qs.filter(caregiver=caregiver)
        return qs

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [AdminOnly()]
        return [IsAuthenticated()]


@api_view(['POST'])
@permission_classes([CaregiverOnly])
def visit_checkin(request, pk):
    """
    POST /api/v1/visits/<pk>/checkin/
    Caregiver checks in to a scheduled visit (optionally with GPS coords).
    """
    caregiver = Caregiver.objects.get(user=request.user)
    visit = generics.get_object_or_404(Visit, pk=pk, caregiver=caregiver)

    if visit.status != Visit.Status.SCHEDULED:
        return Response({'detail': 'Visit is not in SCHEDULED status.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = VisitCheckinSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    visit.check_in_lat  = serializer.validated_data.get('lat')
    visit.check_in_lng  = serializer.validated_data.get('lng')
    visit.check_in_time = timezone.now()
    visit.status = Visit.Status.IN_PROGRESS
    visit.save()
    return Response(VisitSerializer(visit).data)


@api_view(['POST'])
@permission_classes([CaregiverOnly])
def visit_checkout(request, pk):
    """
    POST /api/v1/visits/<pk>/checkout/
    Caregiver checks out of an in-progress visit.
    """
    caregiver = Caregiver.objects.get(user=request.user)
    visit = generics.get_object_or_404(Visit, pk=pk, caregiver=caregiver)

    if visit.status != Visit.Status.IN_PROGRESS:
        return Response({'detail': 'Visit is not IN_PROGRESS.'}, status=status.HTTP_400_BAD_REQUEST)

    visit.check_out_time = timezone.now()
    visit.status = Visit.Status.COMPLETED
    visit.save()
    return Response(VisitSerializer(visit).data)


# ---------------------------------------------------------------------------
# Managers CRUD  (Admin only)
# ---------------------------------------------------------------------------

class ManagerListCreateView(generics.ListCreateAPIView):
    """GET /api/v1/managers/   POST /api/v1/managers/"""
    queryset = User.objects.filter(role=User.Role.MANAGER)
    permission_classes = [AdminOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManagerCreateSerializer
        return ManagerSerializer


class ManagerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/v1/managers/<pk>/"""
    queryset = User.objects.filter(role=User.Role.MANAGER)
    permission_classes = [AdminOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ManagerCreateSerializer
        return ManagerSerializer


# ---------------------------------------------------------------------------
# Compliance report  (Admin + Manager)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AdminOrManager])
def compliance_view(request):
    """
    GET /api/v1/compliance/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
    Per-caregiver compliance breakdown.
    """
    today = timezone.now().date()
    default_from = today - timezone.timedelta(days=30)

    date_from_str = request.query_params.get('date_from', str(default_from))
    date_to_str   = request.query_params.get('date_to',   str(today))

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

    caregiver_stats = []
    for caregiver in Caregiver.objects.filter(is_active=True).select_related('user'):
        cv = visits_qs.filter(caregiver=caregiver)
        assigned    = cv.count()
        completed   = cv.filter(status=Visit.Status.COMPLETED).count()
        cancelled   = cv.filter(status=Visit.Status.CANCELLED).count()
        missed      = cv.filter(status=Visit.Status.SCHEDULED, scheduled_date__lt=today).count()
        in_progress = cv.filter(status=Visit.Status.IN_PROGRESS).count()

        late = sum(
            1 for v in cv.filter(check_in_time__isnull=False)
            if v.check_in_time > timezone.make_aware(
                timezone.datetime.combine(v.scheduled_date, v.scheduled_time)
            ) + timezone.timedelta(minutes=15)
        )

        no_notes = cv.filter(status=Visit.Status.COMPLETED, notes='').count()
        expected = assigned - cancelled
        rate = round(completed / expected * 100) if expected > 0 else None

        caregiver_stats.append({
            'caregiver_id':   caregiver.id,
            'caregiver_name': str(caregiver),
            'assigned':       assigned,
            'completed':      completed,
            'cancelled':      cancelled,
            'missed':         missed,
            'in_progress':    in_progress,
            'late':           late,
            'no_notes':       no_notes,
            'rate':           rate,
        })

    total_assigned  = visits_qs.count()
    total_completed = visits_qs.filter(status=Visit.Status.COMPLETED).count()
    total_cancelled = visits_qs.filter(status=Visit.Status.CANCELLED).count()
    total_missed    = visits_qs.filter(status=Visit.Status.SCHEDULED, scheduled_date__lt=today).count()
    total_closed    = total_assigned - total_cancelled
    overall_rate    = round(total_completed / total_closed * 100) if total_closed > 0 else None

    return Response({
        'date_from': date_from_str,
        'date_to':   date_to_str,
        'summary': {
            'assigned':     total_assigned,
            'completed':    total_completed,
            'cancelled':    total_cancelled,
            'missed':       total_missed,
            'overall_rate': overall_rate,
        },
        'caregiver_stats': caregiver_stats,
    })
