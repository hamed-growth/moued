from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier, Event
from unittest.mock import patch

from django.db import DatabaseError, connection, connections, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Competition, CompetitionAnswer, CompetitionQuestion, CompetitionRegistration,
    PointTransaction, Question, User,
)


class CompetitionFixtures:
    def setUp(self):
        now = timezone.now()
        self.contest = Competition.objects.create(
            title="Synthetic contest", status="active", start_date=now - timedelta(hours=1),
            end_date=now + timedelta(hours=1), first_prize_points=50, second_prize_points=30,
            third_prize_points=10, participation_bonus=5,
        )
        self.player = User.objects.create_user(username="player", total_coins=7)
        self.staff = User.objects.create_superuser(username="operator")
        self.finalize_url = reverse("dashboard:competition_finalize", args=[self.contest.pk])

    def registration(self, user=None, **fields):
        return CompetitionRegistration.objects.create(
            competition=self.contest, user=user or self.player, **fields,
        )

    def assert_points(self, user, amounts):
        user.refresh_from_db()
        self.assertEqual(user.total_points, sum(amounts))
        ledger = PointTransaction.objects.filter(user=user, transaction_type="competition")
        self.assertCountEqual(ledger.values_list("points", "coins"), [(amount, 0) for amount in amounts])


class CompetitionIntegrityTests(CompetitionFixtures, TestCase):
    def test_ranking_preserves_unfinished_and_finish_time_order(self):
        now = timezone.now()
        rows = [
            self.registration(total_correct=3, score=1),
            self.registration(User.objects.create_user(username="early"), total_correct=3,
                              finished_at=now, is_completed=True),
            self.registration(User.objects.create_user(username="late"), total_correct=3,
                              finished_at=now + timedelta(seconds=1), is_completed=True),
            self.registration(User.objects.create_user(username="higher-score"), total_correct=2, score=900),
        ]
        stale = Competition.objects.get(pk=self.contest.pk)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.finalize_url).status_code, 302)
        self.assertEqual(self.client.post(self.finalize_url).status_code, 302)
        self.assertFalse(stale.finalize())
        self.contest.refresh_from_db()
        self.assertEqual(self.contest.status, "finished")
        for row, rank, prizes in zip(rows, (1, 2, 3, None), ([50], [30], [10], []), strict=True):
            row.refresh_from_db()
            self.assertEqual(row.rank, rank)
            self.assert_points(row.user, prizes)
        self.assertFalse(rows[0].is_completed)
        self.assertEqual(rows[0].user.total_coins, 7)

    def test_zero_correct_has_no_rank_or_winner_payout(self):
        reg = self.registration(score=99)
        self.assertTrue(self.contest.finalize())
        reg.refresh_from_db()
        self.assertIsNone(reg.rank)
        self.assert_points(self.player, [])

    def test_later_prize_failure_rolls_back_status_ranks_balances_and_ledger(self):
        first = self.registration(total_correct=3)
        second = self.registration(User.objects.create_user(username="second"), total_correct=2)
        create = PointTransaction.objects.create

        def fail_second(**fields):
            entry = create(**fields)
            if fields["user_id"] == second.user_id:
                raise DatabaseError("synthetic prize error")
            return entry

        self.client.force_login(self.staff)
        with patch.object(PointTransaction.objects, "create", side_effect=fail_second):
            with self.assertLogs("dashboard.views", "ERROR"):
                result = self.client.post(self.finalize_url)
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("synthetic prize error", result.content.decode())
        self.contest.refresh_from_db()
        self.assertEqual(self.contest.status, "active")
        for reg in (first, second):
            reg.refresh_from_db()
            self.assertIsNone(reg.rank)
            self.assert_points(reg.user, [])
        self.assertTrue(self.contest.finalize())

    def test_failure_reading_winners_after_claim_rolls_back_status(self):
        with patch.object(Competition.objects, "get", side_effect=DatabaseError("synthetic read error")):
            with self.assertRaises(DatabaseError):
                self.contest.finalize()
        self.contest.refresh_from_db()
        self.assertEqual(self.contest.status, "active")
        self.assert_points(self.player, [])

    def test_finish_uses_persisted_score_and_cannot_pay_stale_retry(self):
        reg = self.registration(score=2, total_correct=1)
        CompetitionRegistration.objects.filter(pk=reg.pk).update(score=12)
        stale = CompetitionRegistration.objects.get(pk=reg.pk)
        self.client.force_login(self.player)
        url = reverse("missions:finish_competition", args=[self.contest.pk])
        response = self.client.post(url)
        self.assertEqual((response.status_code, response.json()["score"]), (200, 12))
        self.assertFalse(stale.finish())
        self.assertEqual(self.client.post(url).status_code, 400)
        reg.refresh_from_db()
        self.assertTrue(reg.is_completed)
        self.assertIsNotNone(reg.finished_at)
        self.assert_points(self.player, [12, 5])
        self.assertEqual(self.player.total_coins, 7)

    def test_participation_payout_failure_rolls_back_finish_and_answer_reward(self):
        reg = self.registration(score=12)
        create = PointTransaction.objects.create

        def fail_participation(**fields):
            entry = create(**fields)
            if fields["points"] == 5:
                raise DatabaseError("synthetic participation error")
            return entry

        with patch.object(PointTransaction.objects, "create", side_effect=fail_participation):
            with self.assertRaises(DatabaseError):
                reg.finish()
        reg.refresh_from_db()
        self.assertFalse(reg.is_completed)
        self.assertIsNone(reg.finished_at)
        self.assertEqual(reg.score, 12)
        self.assert_points(self.player, [])

    def test_unauthorized_dashboard_post_cannot_finalize(self):
        self.registration(total_correct=2)
        for user in (None, self.player):
            if user:
                self.client.force_login(user)
            self.assertEqual(self.client.post(self.finalize_url).status_code, 302)
        self.contest.refresh_from_db()
        self.assertEqual(self.contest.status, "active")
        self.assert_points(self.player, [])

    def test_admin_action_finalizes_and_activation_cannot_reopen(self):
        reg = self.registration(total_correct=2)
        self.client.force_login(self.staff)
        url = reverse("admin:missions_competition_changelist")
        for action in ("finalize_competition", "activate_competitions", "finalize_competition"):
            response = self.client.post(url, {"action": action, "_selected_action": [self.contest.pk], "index": "0"})
            self.assertEqual(response.status_code, 302)
        self.contest.refresh_from_db()
        reg.refresh_from_db()
        self.assertEqual((self.contest.status, reg.rank), ("finished", 1))
        self.assert_points(self.player, [50])

    def test_admin_form_status_is_guarded(self):
        from .admin import CompetitionAdminForm
        from django.forms import modelform_factory

        form = modelform_factory(Competition, form=CompetitionAdminForm, fields=["status"])
        self.assertFalse(form({"status": "finished"}, instance=self.contest).is_valid())
        self.assertTrue(form({"status": "cancelled"}, instance=self.contest).is_valid())
        self.client.force_login(self.staff)
        self.contest.finalize()
        url = reverse("admin:missions_competition_change", args=[self.contest.pk])
        self.assertNotIn("status", self.client.get(url).context["adminform"].form.fields)


class CompetitionConcurrencyTests(CompetitionFixtures, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(Path(connection.settings_dict["NAME"]).is_file())

    def run_worker(self, task):
        try:
            return task()
        finally:
            connections.close_all()

    def race(self, left, right):
        ready = Barrier(2, timeout=10)

        def start(model, pk, method):
            obj = model.objects.get(pk=pk)
            ready.wait()
            return getattr(obj, method)()

        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(self.run_worker, lambda args=args: start(*args)) for args in (left, right)]
            return [job.result(timeout=20) for job in jobs]

    def test_two_finalizers_only_one_pays(self):
        reg = self.registration(total_correct=2)
        op = (Competition, self.contest.pk, "finalize")
        self.assertCountEqual(self.race(op, op), [True, False])
        self.contest.refresh_from_db()
        reg.refresh_from_db()
        self.assertEqual((self.contest.status, reg.rank), ("finished", 1))
        self.assert_points(self.player, [50])

    def test_two_participant_finish_calls_only_one_pays(self):
        reg = self.registration(score=12)
        op = (CompetitionRegistration, reg.pk, "finish")
        self.assertCountEqual(self.race(op, op), [True, False])
        reg.refresh_from_db()
        self.assertTrue(reg.is_completed)
        self.assertIsNotNone(reg.finished_at)
        self.assert_points(self.player, [12, 5])

    def test_finalization_and_finish_both_preserve_distinct_rewards(self):
        reg = self.registration(total_correct=2, score=12)
        self.assertEqual(self.race(
            (Competition, self.contest.pk, "finalize"),
            (CompetitionRegistration, reg.pk, "finish"),
        ), [True, True])
        reg.refresh_from_db()
        self.contest.refresh_from_db()
        self.assertEqual((self.contest.status, reg.rank, reg.is_completed), ("finished", 1, True))
        self.assertIsNotNone(reg.finished_at)
        self.assert_points(self.player, [50, 12, 5])

    def test_answer_past_eligibility_check_can_land_after_finalization(self):
        reg = self.registration()
        question = Question.objects.create(text="Fixture", option_1="A", option_2="B",
                                           option_3="C", option_4="D", correct_option=1)
        CompetitionQuestion.objects.create(competition=self.contest, question=question)
        client = Client()
        client.force_login(self.player)
        url = reverse("missions:submit_answer", args=[self.contest.pk, question.pk])
        ready, finalized = Event(), Event()
        get_points = CompetitionQuestion.get_points

        def pause_after_checks(link):
            ready.set()
            if not finalized.wait(10):
                raise TimeoutError("Finalization did not complete")
            return get_points(link)

        with patch.object(CompetitionQuestion, "get_points", pause_after_checks):
            with ThreadPoolExecutor(max_workers=1) as pool:
                job = pool.submit(self.run_worker, lambda: client.post(url, {"option": 1}))
                try:
                    self.assertTrue(ready.wait(10))
                    self.assertTrue(self.contest.finalize())
                finally:
                    finalized.set()
                self.assertEqual(job.result(timeout=20).status_code, 200)
        reg.refresh_from_db()
        self.contest.refresh_from_db()
        self.assertEqual((self.contest.status, reg.total_correct, reg.rank), ("finished", 1, None))
        self.assertEqual(CompetitionAnswer.objects.filter(registration=reg, is_correct=True).count(), 1)
        self.assert_points(self.player, [])

    def test_real_sqlite_lock_returns_failure_without_payout(self):
        reg = self.registration(total_correct=2)
        client = Client()
        client.force_login(self.staff)

        def attempt():
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA busy_timeout = 0")
            return client.post(self.finalize_url)

        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Competition.objects.filter(pk=self.contest.pk).update(status="active")
                with self.assertLogs("dashboard.views", "ERROR") as logs:
                    response = pool.submit(self.run_worker, attempt).result(timeout=10)
        self.assertIn("database is locked", "\n".join(logs.output))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("locked", response.content.decode())
        self.contest.refresh_from_db()
        reg.refresh_from_db()
        self.assertEqual((self.contest.status, reg.rank), ("active", None))
        self.assert_points(self.player, [])
