import datetime
import json
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Caregiver, Client, User, Visit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_admin(username='admin', password='pass'):
    return User.objects.create_user(username, password=password, role=User.Role.ADMIN)


def make_manager(username='manager', password='pass'):
    return User.objects.create_user(username, password=password, role=User.Role.MANAGER)


def make_caregiver_user(username='caregiver', password='pass'):
    user = User.objects.create_user(
        username, password=password,
        first_name='Test', last_name='CG',
        role=User.Role.CAREGIVER,
    )
    caregiver = Caregiver.objects.create(
        user=user, first_name='Test', last_name='CG', is_active=True,
    )
    return user, caregiver


def make_client():
    return Client.objects.create(
        first_name='Jane', last_name='Doe',
        address='1 Main St', is_active=True,
    )


def make_visit(caregiver, client, days_offset=0, status=Visit.Status.SCHEDULED):
    date = timezone.now().date() + datetime.timedelta(days=days_offset)
    return Visit.objects.create(
        caregiver=caregiver,
        client=client,
        scheduled_date=date,
        scheduled_time=datetime.time(9, 0),
        status=status,
    )


# ---------------------------------------------------------------------------
# Authentication & role redirect tests
# ---------------------------------------------------------------------------

class AuthTests(TestCase):

    def test_root_shows_login_when_unauthenticated(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_admin_redirected_to_admin_dashboard(self):
        make_admin()
        self.client.login(username='admin', password='pass')
        response = self.client.get('/dashboard/', follow=True)
        self.assertRedirects(response, '/accounts/admin-dashboard/')

    def test_manager_redirected_to_manager_dashboard(self):
        make_manager()
        self.client.login(username='manager', password='pass')
        response = self.client.get('/dashboard/', follow=True)
        self.assertRedirects(response, '/accounts/manager-dashboard/')

    def test_caregiver_redirected_to_caregiver_dashboard(self):
        make_caregiver_user()
        self.client.login(username='caregiver', password='pass')
        response = self.client.get('/dashboard/', follow=True)
        self.assertRedirects(response, '/accounts/caregiver-dashboard/')

    def test_unauthenticated_dashboard_redirects_to_login(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/?next=/dashboard/')

    def test_caregiver_cannot_access_admin_dashboard(self):
        make_caregiver_user()
        self.client.login(username='caregiver', password='pass')
        response = self.client.get('/accounts/admin-dashboard/')
        self.assertEqual(response.status_code, 403)

    # --- Fallback: caregiver login failure scenarios ---

    def test_caregiver_login_wrong_password_stays_on_login(self):
        """Caregiver submits the correct username but wrong password — stays on login page."""
        make_caregiver_user()
        response = self.client.post('/accounts/login/', {
            'username': 'caregiver',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_caregiver_login_nonexistent_user_stays_on_login(self):
        """Caregiver submits credentials for a username that does not exist."""
        response = self.client.post('/accounts/login/', {
            'username': 'nobody',
            'password': 'pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_inactive_caregiver_cannot_login(self):
        """A caregiver whose account has been deactivated is refused login."""
        user, _ = make_caregiver_user()
        user.is_active = False
        user.save()
        response = self.client.post('/accounts/login/', {
            'username': 'caregiver',
            'password': 'pass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


# ---------------------------------------------------------------------------
# Self-registration tests
# ---------------------------------------------------------------------------

class RegistrationTests(TestCase):

    def test_register_creates_caregiver_user(self):
        data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@hvcs.com',
            'phone': '0821234567',
            'qualifications': 'None',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post('/accounts/register/', data, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='newuser')
        self.assertEqual(user.role, User.Role.CAREGIVER)
        self.assertTrue(Caregiver.objects.filter(user=user).exists())

    def test_register_logs_in_and_redirects_to_caregiver_dashboard(self):
        data = {
            'username': 'newuser2',
            'first_name': 'New',
            'last_name': 'User',
            'email': '',
            'phone': '',
            'qualifications': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post('/accounts/register/', data, follow=True)
        self.assertRedirects(response, '/accounts/caregiver-dashboard/')


# ---------------------------------------------------------------------------
# Client CRUD tests
# ---------------------------------------------------------------------------

class ClientCRUDTests(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.client_obj = make_client()
        self.client.login(username='admin', password='pass')

    def test_client_list(self):
        response = self.client.get('/accounts/clients/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jane')

    def test_client_create(self):
        response = self.client.post('/accounts/clients/add/', {
            'first_name': 'Bob', 'last_name': 'Smith',
            'address': '2 Other St', 'is_active': True,
        })
        self.assertRedirects(response, '/accounts/clients/')
        self.assertTrue(Client.objects.filter(first_name='Bob').exists())

    def test_client_update(self):
        response = self.client.post(f'/accounts/clients/{self.client_obj.pk}/edit/', {
            'first_name': 'Jane', 'last_name': 'Updated',
            'address': '1 Main St', 'is_active': True,
        })
        self.assertRedirects(response, '/accounts/clients/')
        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.last_name, 'Updated')

    def test_client_delete(self):
        response = self.client.post(f'/accounts/clients/{self.client_obj.pk}/delete/')
        self.assertRedirects(response, '/accounts/clients/')
        self.assertFalse(Client.objects.filter(pk=self.client_obj.pk).exists())


# ---------------------------------------------------------------------------
# Visit CRUD tests
# ---------------------------------------------------------------------------

class VisitCRUDTests(TestCase):

    def setUp(self):
        self.admin = make_admin()
        _, self.caregiver = make_caregiver_user()
        self.client_obj = make_client()
        self.visit = make_visit(self.caregiver, self.client_obj)
        self.client.login(username='admin', password='pass')

    def test_visit_list(self):
        response = self.client.get('/accounts/visits/')
        self.assertEqual(response.status_code, 200)

    def test_visit_list_filter_by_status(self):
        response = self.client.get('/accounts/visits/?status=SCHEDULED')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Scheduled')

    def test_visit_create(self):
        response = self.client.post('/accounts/visits/add/', {
            'caregiver': self.caregiver.pk,
            'client': self.client_obj.pk,
            'scheduled_date': timezone.now().date(),
            'scheduled_time': '10:00',
            'status': 'SCHEDULED',
            'notes': '',
        })
        self.assertRedirects(response, '/accounts/visits/')

    def test_visit_delete(self):
        response = self.client.post(f'/accounts/visits/{self.visit.pk}/delete/')
        self.assertRedirects(response, '/accounts/visits/')
        self.assertFalse(Visit.objects.filter(pk=self.visit.pk).exists())


# ---------------------------------------------------------------------------
# GPS check-in / check-out tests
# ---------------------------------------------------------------------------

class CheckInOutTests(TestCase):

    def setUp(self):
        self.user, self.caregiver = make_caregiver_user()
        self.client_obj = make_client()
        self.visit = make_visit(self.caregiver, self.client_obj)
        self.client.login(username='caregiver', password='pass')

    def test_checkin_without_gps(self):
        response = self.client.post(
            f'/accounts/caregiver-dashboard/visits/{self.visit.pk}/checkin/', {}
        )
        self.assertRedirects(response, f'/accounts/caregiver-dashboard/visits/{self.visit.pk}/')
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, Visit.Status.IN_PROGRESS)
        self.assertIsNotNone(self.visit.check_in_time)

    def test_checkin_with_gps(self):
        response = self.client.post(
            f'/accounts/caregiver-dashboard/visits/{self.visit.pk}/checkin/',
            {'lat': '-26.204103', 'lng': '28.047305'},
        )
        self.visit.refresh_from_db()
        self.assertIsNotNone(self.visit.check_in_lat)

    def test_checkout_after_checkin(self):
        self.visit.status = Visit.Status.IN_PROGRESS
        self.visit.check_in_time = timezone.now()
        self.visit.save()
        response = self.client.post(
            f'/accounts/caregiver-dashboard/visits/{self.visit.pk}/checkout/'
        )
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, Visit.Status.COMPLETED)
        self.assertIsNotNone(self.visit.check_out_time)

    def test_caregiver_cannot_checkin_others_visit(self):
        other_user, other_caregiver = make_caregiver_user(username='other')
        other_visit = make_visit(other_caregiver, self.client_obj)
        response = self.client.post(
            f'/accounts/caregiver-dashboard/visits/{other_visit.pk}/checkin/', {}
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# OpenStreetMap Nominatim reverse-geocoding tests
# ---------------------------------------------------------------------------

class ReverseGeocodeTests(TestCase):
    """Unit and integration tests for the Nominatim reverse-geocoding helper."""

    def _mock_urlopen(self, display_name):
        """Return a context-manager mock that yields a Nominatim JSON response."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'display_name': display_name}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch('accounts.views.urllib.request.urlopen')
    def test_returns_display_name_from_api(self, mock_urlopen):
        """reverse_geocode returns the display_name from a successful API response."""
        from accounts.views import reverse_geocode
        mock_urlopen.return_value = self._mock_urlopen('14 Main Street, Johannesburg, South Africa')
        result = reverse_geocode('-26.204103', '28.047305')
        self.assertEqual(result, '14 Main Street, Johannesburg, South Africa')

    @patch('accounts.views.urllib.request.urlopen', side_effect=Exception('Network error'))
    def test_returns_empty_string_on_network_failure(self, mock_urlopen):
        """reverse_geocode returns '' silently when the API is unreachable."""
        from accounts.views import reverse_geocode
        result = reverse_geocode('-26.204103', '28.047305')
        self.assertEqual(result, '')

    @patch('accounts.views.urllib.request.urlopen')
    def test_checkin_with_gps_saves_resolved_address(self, mock_urlopen):
        """check-in view populates check_in_address via the Nominatim API."""
        mock_urlopen.return_value = self._mock_urlopen('22 Oak Avenue, Sandton, Gauteng')
        user, caregiver = make_caregiver_user(username='cg_geo')
        client_obj = make_client()
        visit = make_visit(caregiver, client_obj)
        self.client.login(username='cg_geo', password='pass')
        self.client.post(
            f'/accounts/caregiver-dashboard/visits/{visit.pk}/checkin/',
            {'lat': '-26.107567', 'lng': '28.056702'},
        )
        visit.refresh_from_db()
        self.assertEqual(visit.check_in_address, '22 Oak Avenue, Sandton, Gauteng')

    @patch('accounts.views.urllib.request.urlopen', side_effect=Exception('timeout'))
    def test_checkin_still_completes_when_geocode_fails(self, mock_urlopen):
        """A Nominatim timeout must not prevent the check-in from completing."""
        user, caregiver = make_caregiver_user(username='cg_fail')
        client_obj = make_client()
        visit = make_visit(caregiver, client_obj)
        self.client.login(username='cg_fail', password='pass')
        self.client.post(
            f'/accounts/caregiver-dashboard/visits/{visit.pk}/checkin/',
            {'lat': '-26.107567', 'lng': '28.056702'},
        )
        visit.refresh_from_db()
        self.assertEqual(visit.status, Visit.Status.IN_PROGRESS)
        self.assertEqual(visit.check_in_address, '')


# ---------------------------------------------------------------------------
# Manager dashboard — caregiver compliance scores tests
# ---------------------------------------------------------------------------

class ManagerComplianceTests(TestCase):

    def setUp(self):
        self.manager = make_manager()
        _, self.caregiver = make_caregiver_user()
        self.client_obj = make_client()
        self.client.login(username='manager', password='pass')

    def test_manager_dashboard_loads(self):
        response = self.client.get('/accounts/manager-dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_compliance_table_in_context(self):
        """caregiver_compliance list is passed to the template."""
        response = self.client.get('/accounts/manager-dashboard/')
        self.assertIn('caregiver_compliance', response.context)

    def test_compliance_rate_100_for_all_completed(self):
        """A caregiver with all visits completed shows 100%."""
        make_visit(self.caregiver, self.client_obj, status=Visit.Status.COMPLETED)
        response = self.client.get('/accounts/manager-dashboard/')
        rows = response.context['caregiver_compliance']
        row = next(r for r in rows if r['caregiver'] == self.caregiver)
        self.assertEqual(row['rate'], 100)

    def test_compliance_rate_none_when_no_visits(self):
        """A caregiver with no visits in the period shows rate=None."""
        response = self.client.get('/accounts/manager-dashboard/')
        rows = response.context['caregiver_compliance']
        row = next(r for r in rows if r['caregiver'] == self.caregiver)
        self.assertIsNone(row['rate'])

    def test_compliance_rate_50_for_half_completed(self):
        """Two visits, one completed → 50% compliance."""
        make_visit(self.caregiver, self.client_obj, status=Visit.Status.COMPLETED)
        make_visit(self.caregiver, self.client_obj, status=Visit.Status.SCHEDULED)
        response = self.client.get('/accounts/manager-dashboard/')
        rows = response.context['caregiver_compliance']
        row = next(r for r in rows if r['caregiver'] == self.caregiver)
        self.assertEqual(row['rate'], 50)

    def test_cancelled_visits_excluded_from_compliance(self):
        """Cancelled visits do not count towards the denominator."""
        make_visit(self.caregiver, self.client_obj, status=Visit.Status.COMPLETED)
        make_visit(self.caregiver, self.client_obj, status=Visit.Status.CANCELLED)
        response = self.client.get('/accounts/manager-dashboard/')
        rows = response.context['caregiver_compliance']
        row = next(r for r in rows if r['caregiver'] == self.caregiver)
        self.assertEqual(row['rate'], 100)


# ---------------------------------------------------------------------------
# Manager dashboard — missing documentation alerts tests
# ---------------------------------------------------------------------------

class MissingDocumentationAlertTests(TestCase):

    def setUp(self):
        self.manager = make_manager()
        _, self.caregiver = make_caregiver_user()
        self.client_obj = make_client()
        self.client.login(username='manager', password='pass')

    def test_completed_visit_without_notes_appears_in_alert(self):
        visit = make_visit(self.caregiver, self.client_obj, status=Visit.Status.COMPLETED)
        visit.notes = ''
        visit.save()
        response = self.client.get('/accounts/manager-dashboard/')
        self.assertIn(visit, response.context['alerts']['missing_notes'])

    def test_completed_visit_with_notes_not_in_alert(self):
        visit = make_visit(self.caregiver, self.client_obj, status=Visit.Status.COMPLETED)
        visit.notes = 'Client was well.'
        visit.save()
        response = self.client.get('/accounts/manager-dashboard/')
        self.assertNotIn(visit, response.context['alerts']['missing_notes'])

    def test_scheduled_visit_without_notes_not_in_alert(self):
        """Only COMPLETED visits with no notes trigger the alert."""
        visit = make_visit(self.caregiver, self.client_obj, status=Visit.Status.SCHEDULED)
        response = self.client.get('/accounts/manager-dashboard/')
        self.assertNotIn(visit, response.context['alerts']['missing_notes'])
