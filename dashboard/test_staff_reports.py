from django.test import TestCase
from django.urls import reverse

from missions.models import Mission, MissionRequest, PointTransaction, User


class StaffReportTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='reporter', is_staff=True)
        self.client.force_login(self.staff)

    def test_report_pages_require_staff_access(self):
        routes = ('missions', 'mission_requests', 'competitions', 'questions',
                  'daily_questions', 'treasure', 'transactions')
        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(f'dashboard:{route}')).status_code, 200)
        self.client.force_login(User.objects.create_user(username='member'))
        for route in routes:
            with self.subTest(route=route):
                self.assertRedirects(
                    self.client.get(reverse(f'dashboard:{route}')),
                    reverse('missions:home'), fetch_redirect_response=False,
                )

    def test_mission_request_filter_preserves_pending_count(self):
        mission = Mission.objects.create(title='Mission')
        MissionRequest.objects.create(user=self.staff, mission=mission, status='pending')
        rejected = MissionRequest.objects.create(user=self.staff, mission=mission, status='rejected')
        response = self.client.get(reverse('dashboard:mission_requests'), {'status': 'rejected'})
        self.assertEqual(list(response.context['requests']), [rejected])
        self.assertEqual(response.context['pending_count'], 1)

    def test_transaction_totals_follow_both_filters(self):
        matching = PointTransaction.objects.create(
            user=self.staff, transaction_type='bonus', title='Match', points=7, coins=2,
        )
        PointTransaction.objects.create(
            user=self.staff, transaction_type='bonus', title='Other', points=100,
        )
        PointTransaction.objects.create(
            user=self.staff, transaction_type='mission', title='Match', points=100,
        )
        response = self.client.get(reverse('dashboard:transactions'), {'type': 'bonus', 'q': ' Match '})
        self.assertEqual(list(response.context['transactions']), [matching])
        self.assertEqual(response.context['total_points'], 7)
        self.assertEqual(response.context['total_coins'], 2)
