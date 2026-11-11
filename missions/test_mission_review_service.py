from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from .models import MissionRequest, PointTransaction
from .services.mission_review import approve_mission_request, reject_mission_request
from .test_mission_rewards import MissionRewardFixtures


class MissionReviewServiceTests(MissionRewardFixtures, TestCase):
    def test_approval_synchronizes_the_supplied_instance_and_preserves_existing_note(self):
        self.request.admin_note = "existing"
        self.request.save(update_fields=["admin_note"])
        self.assertTrue(approve_mission_request(self.request, admin_user=self.reviewer, admin_note=""))
        self.assertEqual(self.request.status, "approved")
        self.assertEqual(self.request.reviewed_by, self.reviewer)
        self.assertEqual((self.request.points_awarded, self.request.coins_awarded), (10, 4))
        self.assert_reward_state("approved", self.reviewer, 10, 4, "existing")

    def test_rejection_synchronizes_instance_and_stale_approval_is_a_noop(self):
        stale = MissionRequest.objects.get(pk=self.request.pk)
        self.assertTrue(reject_mission_request(self.request, admin_user=self.reviewer, admin_note="first"))
        self.assertEqual((self.request.status, self.request.admin_note), ("rejected", "first"))
        self.assertFalse(approve_mission_request(stale, admin_user=self.reviewer))
        self.assertEqual(stale.status, "pending")
        self.assert_reward_state("rejected", self.reviewer, note="first")

    def test_service_propagates_ledger_error_after_rollback(self):
        with patch.object(PointTransaction.objects, "create", side_effect=DatabaseError("fixture")):
            with self.assertRaises(DatabaseError):
                approve_mission_request(self.request, admin_user=self.reviewer, admin_note="rolled back")
        self.assert_reward_state("pending")
