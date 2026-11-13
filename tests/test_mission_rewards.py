from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db import DatabaseError, connection, connections
from django.db.models import QuerySet
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.missions.models import Mission, MissionCompletion, MissionRequest, TeamMission
from apps.teams.models import Team
from apps.wallet.models import PointTransaction


class MissionRewardFixtures:
    def setUp(self):
        self.user = User.objects.create_user(username="player", total_points=20, total_coins=3)
        self.reviewer = User.objects.create_user(username="reviewer", is_staff=True)
        self.mission = Mission.objects.create(title="Fixture", points=10, coins=4)
        self.request = MissionRequest.objects.create(user=self.user, mission=self.mission)

    def assert_reward_state(self, status, reviewer=None, points=0, coins=0, note=None):
        self.request.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(
            (self.request.status, self.request.reviewed_by_id, self.request.admin_note),
            (status, reviewer.pk if reviewer else None, note),
        )
        self.assertEqual(self.request.reviewed_at is not None, reviewer is not None)
        self.assertEqual((self.request.points_awarded, self.request.coins_awarded), (points, coins))
        self.assertEqual((self.user.total_points, self.user.total_coins), (20 + points, 3 + coins))
        expected = [(points, coins)] if status == "approved" else []
        self.assertEqual(list(MissionCompletion.objects.filter(
            user=self.user, mission=self.mission, team_id=self.request.team_id,
        ).values_list("points_awarded", "coins_awarded")), expected)
        self.assertEqual(MissionCompletion.objects.count(), len(expected))
        self.assertEqual(list(PointTransaction.objects.filter(
            user=self.user, transaction_type="mission",
        ).values_list("points", "coins")), expected)
        self.assertEqual(PointTransaction.objects.count(), len(expected))


class MissionRewardTests(MissionRewardFixtures, TestCase):
    def approve_url(self):
        return reverse("dashboard:mission_request_approve", args=[self.request.pk])

    def test_dashboard_approval_and_stale_instance_cannot_repeat_reward(self):
        stale = MissionRequest.objects.get(pk=self.request.pk)
        self.client.force_login(self.reviewer)
        self.assertEqual(self.client.post(self.approve_url()).status_code, 302)
        stale.note = "Edited from old form"
        stale.save()
        self.assertFalse(stale.approve(admin_user=self.reviewer))
        self.assertFalse(stale.reject(admin_user=self.reviewer))
        self.assert_reward_state("approved", self.reviewer, 10, 4)
        self.assertEqual(self.request.note, "Edited from old form")

    def test_team_override_used_for_all_reward_records(self):
        team = Team.objects.create(name="Fixture team")
        TeamMission.objects.create(team=team, mission=self.mission, points_override=6, coins_override=9)
        self.request.team = team
        self.request.save(update_fields=["team"])
        self.assertTrue(self.request.approve(admin_user=self.reviewer))
        self.assert_reward_state("approved", self.reviewer, 6, 9)

    def test_rejection_and_repeat_preserve_first_review(self):
        self.assertTrue(self.request.reject(admin_user=self.reviewer, admin_note="first"))
        self.assertFalse(self.request.reject(admin_user=self.reviewer, admin_note="second"))
        self.assertFalse(self.request.approve(admin_user=self.reviewer))
        self.assert_reward_state("rejected", self.reviewer, note="first")

    def test_dashboard_unauthorized_cannot_approve(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.post(self.approve_url()), reverse("missions:home"),
                             fetch_redirect_response=False)
        self.assert_reward_state("pending")

    def test_admin_action_uses_approval_path_and_requires_change_permission(self):
        view = Permission.objects.get(content_type__app_label="missions", codename="view_missionrequest")
        change = Permission.objects.get(content_type__app_label="missions", codename="change_missionrequest")
        self.reviewer.user_permissions.add(view)
        self.client.force_login(self.reviewer)
        url = reverse("admin:missions_missionrequest_changelist")
        payload = {"action": "approve_requests", "_selected_action": [self.request.pk], "index": "0"}
        self.client.post(url, payload)
        self.assert_reward_state("pending")
        self.reviewer.user_permissions.add(change)
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.assert_reward_state("approved", self.reviewer, 10, 4)
        self.client.post(url, payload)
        self.assert_reward_state("approved", self.reviewer, 10, 4)

    def test_admin_form_cannot_set_status_directly(self):
        self.reviewer.user_permissions.add(Permission.objects.get(
            content_type__app_label="missions", codename="change_missionrequest",
        ))
        self.client.force_login(self.reviewer)
        url = reverse("admin:missions_missionrequest_change", args=[self.request.pk])
        response = self.client.post(url, {
            "user": self.user.pk, "mission": self.mission.pk, "status": "approved", "note": "safe edit",
        })
        self.assertEqual(response.status_code, 302)
        self.assert_reward_state("pending")
        self.assertEqual(self.request.note, "safe edit")

    def test_completion_or_ledger_failure_rolls_back(self):
        self.client.force_login(self.reviewer)
        for manager in (MissionCompletion.objects, PointTransaction.objects):
            with self.subTest(model=manager.model):
                create = manager.create

                def fail_after_create(**kwargs):
                    create(**kwargs)
                    raise DatabaseError("synthetic write error")

                with patch.object(manager, "create", side_effect=fail_after_create):
                    with self.assertLogs("apps.missions.staff_views", "ERROR"):
                        response = self.client.post(self.approve_url())
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("synthetic write error", response.content.decode())
                self.assert_reward_state("pending")

    def test_balance_failure_rolls_back_completion_and_review(self):
        update = QuerySet.update

        def fail_after_balance(queryset, **kwargs):
            result = update(queryset, **kwargs)
            if queryset.model is User:
                raise DatabaseError("synthetic balance write error")
            return result

        with patch.object(QuerySet, "update", fail_after_balance):
            with self.assertRaises(DatabaseError):
                self.request.approve(admin_user=self.reviewer, admin_note="rolled back")
        self.assert_reward_state("pending")
        self.assertTrue(self.request.approve(admin_user=self.reviewer))
        self.assert_reward_state("approved", self.reviewer, 10, 4)


class MissionRewardConcurrencyTests(MissionRewardFixtures, TransactionTestCase):
    def race(self, methods):
        self.assertEqual(connection.vendor, "sqlite")
        self.assertTrue(Path(connection.settings_dict["NAME"]).is_file())
        other = User.objects.create_user(username="other-reviewer", is_staff=True)
        reviewers = (self.reviewer, other)
        ready = Barrier(2, timeout=10)

        def review(method, reviewer):
            try:
                request = MissionRequest.objects.get(pk=self.request.pk)
                ready.wait()
                return getattr(request, method)(admin_user=reviewer, admin_note=method)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as workers:
            jobs = [workers.submit(review, method, reviewer)
                    for method, reviewer in zip(methods, reviewers, strict=True)]
            results = [job.result(timeout=20) for job in jobs]
        self.assertCountEqual(results, [True, False])
        winner = results.index(True)
        return methods[winner], reviewers[winner]

    def test_two_approvals_issue_one_reward(self):
        _, reviewer = self.race(("approve", "approve"))
        self.assert_reward_state("approved", reviewer, 10, 4, "approve")

    def test_approval_and_rejection_have_one_winner(self):
        method, reviewer = self.race(("approve", "reject"))
        if method == "approve":
            self.assert_reward_state("approved", reviewer, 10, 4, "approve")
        else:
            self.assert_reward_state("rejected", reviewer, note="reject")
