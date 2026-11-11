"""Characterization tests using only synthetic records."""
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Competition, CompetitionQuestion, CompetitionRegistration, DailyQuestion,
    Mission, MissionRequest, PointTransaction, Question, Team, TeamMember,
    TreasureItem, TreasurePurchase, User,
)


class BehavioralBaseline(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="baseline-player")
        self.staff = User.objects.create_user(username="baseline-staff", is_staff=True)

    def post(self, route, *args, **data):
        return self.client.post(reverse(route, args=args), data)

    def assert_balance(self, points, coins):
        self.user.refresh_from_db()
        self.assertEqual((self.user.total_points, self.user.total_coins), (points, coins))

    def question(self):
        return Question.objects.create(
            text="Synthetic question", option_1="A", option_2="B",
            option_3="C", option_4="D", correct_option=1,
        )

    def competition(self):
        now = timezone.now()
        return Competition.objects.create(
            title="Synthetic contest", status="active",
            start_date=now - timedelta(hours=1), end_date=now + timedelta(hours=1),
        )

    def test_registration_and_login(self):
        password = "synthetic-password-93"
        self.assertEqual(self.post(
            "missions:register", username="baseline-new", email="new@example.invalid",
            password1=password, password2=password,
        ).status_code, 302)
        registered = User.objects.get(username="baseline-new")
        self.assertEqual(int(self.client.session["_auth_user_id"]), registered.pk)
        self.assertEqual(self.client.get(reverse("missions:logout")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.post(
            "missions:login", username=registered.username, password=password,
        ).status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), registered.pk)

    def test_team_membership_is_unique_per_user(self):
        team = Team.objects.create(name="Team A")
        TeamMember.objects.create(team=team, user=self.user)
        self.assertEqual(self.user.team_membership.team, team)
        other = Team.objects.create(name="Team B")
        with self.assertRaises(IntegrityError), transaction.atomic():
            TeamMember.objects.create(team=other, user=self.user)

    def test_mission_request_and_duplicate(self):
        self.client.force_login(self.user)
        mission = Mission.objects.create(title="Synthetic mission", is_global=True)
        response = self.post("missions:request_mission", mission.pk, note=" fixture ")
        self.assertTrue(response.json()["success"])
        req = MissionRequest.objects.get(pk=response.json()["request_id"])
        self.assertEqual((req.user, req.status, req.note), (self.user, "pending", "fixture"))
        self.assertEqual(self.post("missions:request_mission", mission.pk).status_code, 400)

    def test_mission_approval_cannot_be_reopened_by_rejection(self):
        mission = Mission.objects.create(title="Synthetic mission", points=10, coins=4)
        req = MissionRequest.objects.create(user=self.user, mission=mission)
        self.client.force_login(self.staff)
        approve = "dashboard:mission_request_approve"
        self.assertEqual(self.post(approve, req.pk).status_code, 302)
        self.post(approve, req.pk)
        self.assert_balance(10, 4)
        self.post("dashboard:mission_request_reject", req.pk, admin_note="fixture")
        req.refresh_from_db()
        self.assertEqual((req.status, req.admin_note), ("approved", None))
        self.assert_balance(10, 4)
        self.post(approve, req.pk)
        self.assert_balance(10, 4)
        self.assertEqual(
            list(PointTransaction.objects.filter(user=self.user).values_list("points", "coins")),
            [(10, 4)],
        )

    def test_daily_answer_rewards_points_once(self):
        self.client.force_login(self.user)
        daily = DailyQuestion.objects.create(question=self.question(), points=7)
        response = self.post("missions:answer_daily", daily.pk, option=1)
        self.assertTrue(response.json()["is_correct"])
        self.assertEqual(self.post("missions:answer_daily", daily.pk, option=1).status_code, 400)
        self.assert_balance(7, 0)
        self.assertEqual(PointTransaction.objects.filter(user=self.user).count(), 1)

    def test_competition_registration_repeat_keeps_one_record(self):
        self.client.force_login(self.user)
        contest = self.competition()
        for _ in range(2):
            self.assertEqual(self.post("missions:register_competition", contest.pk).status_code, 302)
        self.assertEqual(CompetitionRegistration.objects.filter(competition=contest, user=self.user).count(), 1)

    def test_competition_answer_requires_registration_and_awards_on_finish(self):
        self.client.force_login(self.user)
        contest = self.competition()
        contest.max_questions = 1
        contest.save(update_fields=["max_questions"])
        question = self.question()
        CompetitionQuestion.objects.create(competition=contest, question=question)
        route = "missions:submit_answer"
        self.assertEqual(self.post(route, contest.pk, question.pk, option=1).status_code, 400)
        self.post("missions:register_competition", contest.pk)
        result = self.post(route, contest.pk, question.pk, option=1).json()
        self.assertEqual((result["score"], result["is_completed"]), (10, True))
        self.assert_balance(30, 0)
        self.assertEqual(self.post(route, contest.pk, question.pk, option=1).status_code, 400)
        self.assertEqual(PointTransaction.objects.filter(user=self.user).count(), 2)

    def test_competition_finalization_ranks_by_correct_count(self):
        contest = self.competition()
        winner = CompetitionRegistration.objects.create(
            competition=contest, user=self.user, total_correct=2, score=10,
        )
        other = CompetitionRegistration.objects.create(
            competition=contest, user=self.staff, total_correct=1, score=100,
        )
        self.client.force_login(self.staff)
        for _ in range(2):
            self.assertEqual(self.post("dashboard:competition_finalize", contest.pk).status_code, 302)
        contest.refresh_from_db()
        winner.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((contest.status, winner.rank, other.rank), ("finished", 1, 2))
        self.assert_balance(contest.first_prize_points, 0)
        self.assertEqual(PointTransaction.objects.filter(user=self.user).count(), 1)

    def test_treasure_purchase_spends_points_and_decrements_stock(self):
        self.user.total_points, self.user.total_coins = 20, 2
        self.user.save()
        self.client.force_login(self.user)
        item = TreasureItem.objects.create(name="Fixture", image="fixture.png", price=12, stock=1)
        self.assertTrue(self.post("missions:buy_treasure_item", item.pk).json()["success"])
        self.assertEqual(self.post("missions:buy_treasure_item", item.pk).status_code, 400)
        item.refresh_from_db()
        self.assertEqual(item.stock, 0)
        self.assert_balance(8, 2)
        purchase = TreasurePurchase.objects.get(user=self.user, item=item)
        debit = PointTransaction.objects.get(user=self.user)
        self.assertEqual((purchase.status, debit.points, debit.coins), ("pending", -12, 0))

    def test_dashboard_redirects_regular_user_and_denies_staff_role_toggle(self):
        route = "dashboard:user_toggle_staff"
        self.client.force_login(self.user)
        self.assertRedirects(
            self.post(route, self.user.pk), reverse("missions:home"),
            fetch_redirect_response=False,
        )
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.client.force_login(self.staff)
        self.assertEqual(self.post(route, self.user.pk).status_code, 403)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)


class ExpectedSecureBehavior(TestCase):
    def test_ordinary_staff_cannot_grant_staff_privileges(self):
        staff = User.objects.create_user(username="staff", is_staff=True)
        target = User.objects.create_user(username="target")
        self.client.force_login(staff)
        self.client.post(reverse("dashboard:user_toggle_staff", args=[target.pk]))
        target.refresh_from_db()
        self.assertFalse(target.is_staff)
