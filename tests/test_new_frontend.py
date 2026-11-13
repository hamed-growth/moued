from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class NewFrontendTests(TestCase):
    def test_root_is_login_and_dashboard_is_protected(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'خوش برگشتی')
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/?next=/dashboard/', fetch_redirect_response=False)

    def test_login_opens_empty_dashboard(self):
        User.objects.create_user(username='member', password='A-long-test-password-42')
        response = self.client.post('/', {'username': 'member', 'password': 'A-long-test-password-42'})
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertContains(self.client.get('/dashboard/'), 'من داشبورد هستم')

    def test_logout_requires_post(self):
        User.objects.create_user(username='member', password='A-long-test-password-42')
        self.client.login(username='member', password='A-long-test-password-42')
        self.assertEqual(self.client.get(reverse('missions:logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('missions:logout')), '/', fetch_redirect_response=False)

    def test_registration_page_and_signup(self):
        response = self.client.get(reverse('missions:register'))
        self.assertContains(response, 'به باشگاه بپیوند')
        self.assertContains(response, 'data-password-strength')
        self.assertNotContains(response, 'name="password2"')
        response = self.client.post(reverse('missions:register'), {
            'username': 'new_member',
            'email': 'new_member@example.com',
            'password': 'A-long-test-password-42',
        })
        self.assertRedirects(response, '/missions/', fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username='new_member').exists())

    def test_login_with_email_and_remember_me(self):
        User.objects.create_user(username='member', email='member@example.com', password='A-long-test-password-42')
        response = self.client.post('/', {
            'username': 'member@example.com', 'password': 'A-long-test-password-42', 'remember_me': 'on',
        })
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertGreater(self.client.session.get_expiry_age(), 60 * 60 * 24 * 80)

    def test_login_without_remember_me_ends_with_browser(self):
        User.objects.create_user(username='member', password='A-long-test-password-42')
        response = self.client.post('/', {'username': 'member', 'password': 'A-long-test-password-42'})
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_error_is_generic(self):
        response = self.client.post('/', {'username': 'unknown', 'password': 'wrong'})
        self.assertContains(response, 'نام کاربری یا گذرواژه درست نیست')

    def test_signup_rejects_short_password_without_javascript(self):
        response = self.client.post(reverse('missions:register'), {
            'username': 'new_member', 'email': 'new_member@example.com', 'password': 'short',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-invalid="true"')
        self.assertFalse(User.objects.filter(username='new_member').exists())

    def test_signup_requires_email_without_javascript(self):
        response = self.client.post(reverse('missions:register'), {
            'username': 'new_member', 'password': 'A-long-test-password-42',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='new_member').exists())
