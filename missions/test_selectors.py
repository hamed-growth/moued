from datetime import datetime, timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from .models import (
    Competition, CompetitionRegistration, Mission, MissionCompletion, MissionRequest,
    PointTransaction, Team, TeamMember, User,
)
from .selectors.leagues import get_league_rankings
from .selectors.profiles import get_profile_history, get_profile_rank


class ProfileLeagueSelectorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner", total_points=8)
        self.other = User.objects.create_user(username="other", total_points=12)

    def test_profile_history_is_private_and_limited_to_ten_newest(self):
        mission = Mission.objects.create(title="Fixture")
        rows = MissionCompletion.objects.bulk_create([
            MissionCompletion(user=self.user, mission=mission) for _ in range(11)
        ] + [MissionCompletion(user=self.other, mission=mission)])
        now = timezone.now()
        for offset, row in enumerate(rows):
            MissionCompletion.objects.filter(pk=row.pk).update(completed_at=now + timedelta(seconds=offset))
        competition = Competition.objects.create(title="Fixture", start_date=now, end_date=now + timedelta(days=1))
        registration = CompetitionRegistration.objects.create(user=self.user, competition=competition)
        CompetitionRegistration.objects.create(user=self.other, competition=competition)
        with CaptureQueriesContext(connection) as queries:
            count, completions, registrations = get_profile_history(self.user)
            self.assertEqual(count, 11)
            self.assertEqual([c.pk for c in completions], [row.pk for row in reversed(rows[1:11])])
            self.assertEqual(list(registrations), [registration])
        self.assertEqual(len(queries), 3)
        self.assertTrue(all(query["sql"].startswith("SELECT") for query in queries))
        self.client.force_login(self.user)
        response = self.client.get(reverse("missions:profile"))
        self.assertTemplateUsed(response, "missions/profile.html")
        self.assertEqual(response.context["completions_count"], 11)
        self.assertEqual(list(response.context["registrations"]), [registration])

    def test_active_rank_counts_ties_and_ignores_inactive_users(self):
        User.objects.create_user(username="tie", total_points=8)
        User.objects.create_user(username="inactive", total_points=100, is_active=False)
        with self.assertNumQueries(1):
            self.assertEqual(get_profile_rank(self.user), (2, 3))

    def test_league_rankings_use_one_prefetch_and_keep_negative_points(self):
        mine = Team.objects.create(name="Mine", manager=self.user)
        rival = Team.objects.create(name="Rival")
        empty = Team.objects.create(name="Empty")
        TeamMember.objects.create(user=self.user, team=mine)
        TeamMember.objects.create(user=self.other, team=rival)
        with CaptureQueriesContext(connection) as queries:
            my_team, teams = get_league_rankings(self.user, mine, {self.user.pk: -2, self.other.pk: 4})
        self.assertEqual(len(queries), 4)
        self.assertTrue(all(query["sql"].startswith("SELECT") for query in queries))
        self.assertEqual(
            [(t["id"], t["rank"], t["total_points"]) for t in teams],
            [(rival.pk, 1, 4), (empty.pk, 2, 0), (mine.pk, 3, -2)],
        )
        self.assertEqual(teams[1]["top_members"], [])
        self.assertEqual(teams[2]["manager"], self.user)
        self.assertEqual(my_team["rank"], 3)
        self.assertEqual(my_team["members"], [{"user": self.user, "points": -2, "is_me": True, "rank": 1}])

    def test_authenticated_month_context_and_pending_visibility(self):
        mine = Team.objects.create(name="Mine")
        TeamMember.objects.create(user=self.user, team=mine)
        for user, points in ((self.user, 8), (self.other, 90)):
            row = PointTransaction.objects.create(user=user, title="Fixture", points=points, coins=3)
            PointTransaction.objects.filter(pk=row.pk).update(
                created_at=timezone.make_aware(datetime(2026, 4, 10, 12)),
            )
        mission = Mission.objects.create(title="Fixture", points=4, coins=2)
        requests = MissionRequest.objects.bulk_create([
            MissionRequest(user=self.user, mission=mission) for _ in range(6)
        ] + [MissionRequest(user=self.other, mission=mission)])
        now = timezone.now()
        for offset, row in enumerate(requests):
            MissionRequest.objects.filter(pk=row.pk).update(requested_at=now + timedelta(seconds=offset))
        self.client.force_login(self.user)
        profile = self.client.get(reverse("missions:profile"), {"month": "invalid"})
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.context["selected_month"], "1405-01")
        self.assertEqual(profile.context["month_total"], 8)
        self.assertEqual(profile.context["month_coins"], 3)
        self.assertEqual(profile.context["pending_count"], 6)
        self.assertEqual(profile.context["pending_points"], 24)
        self.assertEqual(list(profile.context["pending_requests"]), list(reversed(requests[1:6])))
        league = self.client.get(reverse("missions:league_list"), {"month": "1405-02"})
        self.assertEqual(league.status_code, 200)
        self.assertTemplateUsed(league, "missions/league_list.html")
        self.assertEqual(league.context["selected_month"], "1405-02")
        self.assertEqual(league.context["my_team_data"]["total_points"], 0)

    def test_empty_context_and_anonymous_redirects(self):
        profile_url = reverse("missions:profile")
        league_url = reverse("missions:league_list")
        for url in (profile_url, league_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, f"/accounts/login/?next={url}")
        self.client.force_login(self.user)
        profile = self.client.get(profile_url)
        self.assertEqual(profile.context["month_options"], [])
        self.assertEqual(profile.context["selected_month"], "")
        self.assertEqual(profile.context["team_leaderboard"], [])
        with patch("missions.views.timezone.localdate", return_value=datetime(2026, 4, 10).date()):
            league = self.client.get(league_url, {"month": "invalid"})
        self.assertEqual(league.context["selected_month"], "1405-01")
        self.assertIsNone(league.context["my_team_data"])
        self.assertEqual(league.context["all_teams"], [])
