import datetime

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
