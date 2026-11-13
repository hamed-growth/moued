from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from apps.accounts.models import User
from apps.competitions.models import Competition, CompetitionRegistration
from apps.wallet.models import PointTransaction
from apps.competitions.services.rewards import finalize_competition, finish_competition_registration
from .test_competition_integrity import CompetitionFixtures


class CompetitionServiceTests(CompetitionFixtures, TestCase):
    def test_finish_uses_stored_score_and_synchronizes_a_losing_instance(self):
        registration = self.registration(score=12)
        stale = CompetitionRegistration.objects.get(pk=registration.pk)
        self.assertTrue(finish_competition_registration(registration))
        self.assertTrue(registration.is_completed)
        self.assertIsNotNone(registration.finished_at)
        self.assertFalse(finish_competition_registration(stale))
        self.assertEqual(stale.finished_at, registration.finished_at)
        self.assert_points(self.player, [12, 5])
        self.assertEqual(self.player.total_coins, 7)

    def test_finalize_ranks_by_correct_count_and_pays_once(self):
        winner = self.registration(total_correct=3, score=2)
        other = User.objects.create_user(username="runner-up", total_coins=3)
        runner_up = self.registration(other, total_correct=2, score=90)
        stale = Competition.objects.get(pk=self.contest.pk)
        self.assertTrue(finalize_competition(self.contest))
        self.assertEqual(self.contest.status, "finished")
        self.assertFalse(finalize_competition(stale))
        self.assertEqual(stale.status, "active")
        winner.refresh_from_db()
        runner_up.refresh_from_db()
        self.assertEqual((winner.rank, runner_up.rank), (1, 2))
        self.assert_points(self.player, [50])
        self.assert_points(other, [30])
        self.assertEqual((self.player.total_coins, other.total_coins), (7, 3))

    def test_failed_payout_rolls_back_both_service_transitions(self):
        registration = self.registration(total_correct=3, score=12)
        with patch.object(PointTransaction.objects, "create", side_effect=DatabaseError("fixture")):
            with self.assertRaises(DatabaseError):
                finish_competition_registration(registration)
            with self.assertRaises(DatabaseError):
                finalize_competition(self.contest)
        registration.refresh_from_db()
        self.contest.refresh_from_db()
        self.assertFalse(registration.is_completed)
        self.assertIsNone(registration.finished_at)
        self.assertIsNone(registration.rank)
        self.assertEqual(self.contest.status, "active")
        self.assert_points(self.player, [])
