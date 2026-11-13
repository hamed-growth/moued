from django.test import TestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.missions.models import Mission, TeamMission
from apps.teams.models import Team, TeamMember


class StaffTeamReadTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff', is_staff=True)
        self.user = User.objects.create_user(username='member', total_points=12)
        self.team = Team.objects.create(name='Populated')
        self.empty = Team.objects.create(name='Empty')
        TeamMember.objects.create(user=self.user, team=self.team)
        self.active = Mission.objects.create(title='Active')
        self.inactive = Mission.objects.create(title='Inactive', is_active=False)
        TeamMission.objects.create(team=self.team, mission=self.active, is_active=True)
        TeamMission.objects.create(team=self.team, mission=self.inactive, is_active=False)
        self.client.force_login(self.staff)

    def test_team_summary_counts_order_and_empty_team(self):
        response = self.client.get(reverse('dashboard:teams'))
        self.assertEqual(response.status_code, 200)
        teams = list(response.context['teams'])
        self.assertEqual([t.pk for t in teams], [self.team.pk, self.empty.pk])
        self.assertEqual((teams[0].members_count, teams[0].total_points_sum), (1, 12))
        self.assertEqual((teams[1].members_count, teams[1].total_points_sum), (0, None))

    def test_detail_scopes_members_and_active_assignments(self):
        response = self.client.get(reverse('dashboard:team_detail', args=[self.team.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([m.user_id for m in response.context['members']], [self.user.pk])
        self.assertEqual(list(response.context['missions']), [self.active])
        self.assertEqual(response.context['active_team_mission_ids'], {self.active.pk})
        other = self.client.get(reverse('dashboard:team_detail', args=[self.empty.pk]))
        self.assertEqual(list(other.context['members']), [])
        self.assertEqual(other.context['active_team_mission_ids'], set())

    def test_authorization_and_missing_team(self):
        self.assertEqual(self.client.get(reverse('dashboard:team_detail', args=[99999])).status_code, 404)
        self.client.force_login(self.user)
        for url in [reverse('dashboard:teams'), reverse('dashboard:team_detail', args=[self.team.pk])]:
            self.assertRedirects(self.client.get(url), reverse('missions:home'), fetch_redirect_response=False)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('dashboard:teams')).status_code, 302)
