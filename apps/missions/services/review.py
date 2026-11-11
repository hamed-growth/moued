"""Atomic pending-request review. Callers enforce their own authorization."""

from django.db import transaction
from django.utils import timezone

from missions.models import MissionCompletion, MissionRequest


def _review_pending(mission_request, status, admin_user, admin_note):
    updates = {
        'status': status,
        'reviewed_at': timezone.now(),
        'reviewed_by': admin_user,
    }
    if admin_note:
        updates['admin_note'] = admin_note
    return MissionRequest.objects.filter(pk=mission_request.pk, status='pending').update(**updates) == 1


def approve_mission_request(mission_request, admin_user=None, admin_note=None):
    """Approve a pending request and synchronize the supplied instance on success."""
    with transaction.atomic():
        if not _review_pending(mission_request, 'approved', admin_user, admin_note):
            return False
        mission_request.refresh_from_db()
        completion = MissionCompletion.objects.create(
            user_id=mission_request.user_id,
            mission_id=mission_request.mission_id,
            team_id=mission_request.team_id,
        )
        mission_request.points_awarded = completion.points_awarded
        mission_request.coins_awarded = completion.coins_awarded
        MissionRequest.objects.filter(pk=mission_request.pk).update(
            points_awarded=mission_request.points_awarded,
            coins_awarded=mission_request.coins_awarded,
        )
        return True


def reject_mission_request(mission_request, admin_user=None, admin_note=None):
    """Reject a pending request and synchronize the supplied instance on success."""
    with transaction.atomic():
        if not _review_pending(mission_request, 'rejected', admin_user, admin_note):
            return False
        mission_request.refresh_from_db()
        return True
