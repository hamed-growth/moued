from django.test import TestCase, Client
from apps.accounts.models import User
from apps.missions.models import Mission, MissionRequest


class MissionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='mission-api')
        self.staff = User.objects.create_user(username='reviewer', is_staff=True)
        self.mission = Mission.objects.create(title='Daily', is_global=True, points=15, coins=2)
        self.client.force_login(self.user)

    def submit(self):
        return self.client.post(f'/api/v1/missions/{self.mission.pk}/requests/',
                                {'note': 'done'}, content_type='application/json')

    def test_submit_review_and_calendar(self):
        response = self.submit()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.submit().status_code, 409)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_points, 0)
        url = f'/api/v1/staff/mission-requests/{response.json()["id"]}/review/'
        self.assertEqual(self.client.post(url, {'status': 'approved'}, content_type='application/json').status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(url, {'status': 'approved'}, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.post(url, {'status': 'approved'}, content_type='application/json').status_code, 409)
        self.user.refresh_from_db()
        self.assertEqual(self.user.total_points, 15)
        self.client.force_login(self.user)
        result = self.client.get('/api/v1/missions/calendar/').json()
        self.assertEqual(result['days'][0]['missions'][0]['status'], 'approved')
        self.assertEqual(result['summary']['points'], 15)

    def test_access_validation_and_csrf(self):
        private = Mission.objects.create(title='Private')
        self.assertEqual(self.client.post(f'/api/v1/missions/{private.pk}/requests/', {}, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/api/v1/missions/calendar/?start=invalid').status_code, 400)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(f'/api/v1/missions/{self.mission.pk}/requests/', {}, content_type='application/json').status_code, 403)
        self.assertEqual(MissionRequest.objects.count(), 0)
