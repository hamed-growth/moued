from datetime import timedelta, time
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.missions.models import Mission, MissionRequest
from apps.missions.selectors.path import day_range


class MissionPathTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='path_user', password='A-long-test-password-42')
        self.other = User.objects.create_user(username='other_path_user', password='A-long-test-password-42')
        self.mission = Mission.objects.create(title='کار خوب', is_global=True, is_active=True, points=10)
        self.today = timezone.localdate()

    def test_dates_and_user_requests_are_isolated(self):
        MissionRequest.objects.create(user=self.other, mission=self.mission, status='pending')
        days = day_range(self.user, self.today - timedelta(days=1), self.today + timedelta(days=1))
        self.assertEqual([d['nodes'][0]['state'] for d in days], ['missed', 'available', 'locked'])
        MissionRequest.objects.create(user=self.user, mission=self.mission, status='pending')
        self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'pending')

    def test_page_is_protected_and_partial_is_bounded(self):
        self.assertEqual(self.client.get('/missions/').status_code, 302)
        self.assertEqual(self.client.get('/missions/days/?after=2026-11-12').status_code, 401)
        self.client.force_login(self.user)
        page = self.client.get('/missions/')
        self.assertContains(page, 'کار خوب')
        self.assertNotContains(page, f'day-{(self.today - timedelta(days=1)).isoformat()}')
        response = self.client.get(f'/missions/days/?after={self.today.isoformat()}&count=99')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.content.count(b'<section class="mission-day'), 3)

    def test_request_states_and_time_windows(self):
        request = MissionRequest.objects.create(user=self.user, mission=self.mission, status='approved')
        self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'approved')
        MissionRequest.objects.filter(pk=request.pk).update(status='rejected')
        self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'rejected')
        request.delete()
        self.mission.has_time_limit = True
        self.mission.start_time = time(3)
        self.mission.end_time = time(6)
        self.mission.save()
        with patch('apps.missions.selectors.path.timezone.localdate', return_value=self.today), patch('apps.missions.selectors.path.timezone.localtime') as localtime:
            localtime.return_value.time.return_value = time(2)
            self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'not_open')
            localtime.return_value.time.return_value = time(7)
            self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'missed')

    def test_submission_always_uses_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.post(f'/missions/{self.mission.pk}/request/', {'user_id': self.other.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(MissionRequest.objects.filter(user=self.user, mission=self.mission).exists())
        self.assertFalse(MissionRequest.objects.filter(user=self.other, mission=self.mission).exists())

    def test_latest_request_of_day_is_visible_and_rejected_can_retry(self):
        MissionRequest.objects.create(user=self.user, mission=self.mission, status='rejected')
        MissionRequest.objects.create(user=self.user, mission=self.mission, status='pending')
        self.assertEqual(day_range(self.user, self.today, self.today)[0]['nodes'][0]['state'], 'pending')
        MissionRequest.objects.filter(user=self.user, status='pending').delete()
        node = day_range(self.user, self.today, self.today)[0]['nodes'][0]
        self.assertEqual(node['state'], 'rejected')
        self.assertTrue(node['retry_allowed'])
