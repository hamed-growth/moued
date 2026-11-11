from django.test import TestCase
from django.urls import reverse

from missions.models import PointTransaction, Team, TeamMember, User


class StaffAccountReadTests(TestCase):
    def setUp(self):
        staff = User.objects.create_user(username='staff', is_staff=True)
        self.client.force_login(staff)
        self.member = User.objects.create_user(
            username='member', first_name='Match', is_team_manager=True,
        )
        User.objects.create_user(username='another', first_name='Match', is_team_manager=True)
        self.other = User.objects.create_user(username='other', first_name='Match')
        self.team = Team.objects.create(name='Team')
        for user in (self.member, self.other):
            TeamMember.objects.create(team=self.team, user=user)

    def test_search_role_and_team_filters_intersect(self):
        response = self.client.get(reverse('dashboard:users'), {
            'q': ' Match ', 'role': 'manager', 'team': self.team.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['users']), [self.member])
        self.assertEqual(response.context['q'], 'Match')

    def test_detail_history_is_scoped_and_limited(self):
        PointTransaction.objects.bulk_create([
            PointTransaction(user=self.member, title=str(index), points=1)
            for index in range(51)
        ])
        PointTransaction.objects.create(user=self.other, title='Other', points=1)
        url = reverse('dashboard:user_detail', args=[self.member.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        rows = list(response.context['transactions'])
        self.assertEqual(len(rows), 50)
        self.assertEqual({row.user_id for row in rows}, {self.member.pk})
        self.assertEqual(response.context['user_team'], self.team)
        self.client.force_login(self.other)
        self.assertRedirects(self.client.get(url), reverse('missions:home'), fetch_redirect_response=False)
