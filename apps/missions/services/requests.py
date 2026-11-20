from django.db import transaction
from django.db.models import F
from apps.accounts.models import User
"""Submission workflow for the missions domain."""

from apps.missions.models import MissionRequest
from apps.submissions import SubmissionRejected, MissionTeamAccessDenied
from apps.teams.selectors.membership import get_user_team
from apps.missions.selectors.eligibility import has_completed_today, has_pending_request_today


@transaction.atomic
def create_mission_request(user, mission, note):
    # Serialize submissions for one user before checking daily duplicates.
    User.objects.filter(pk=user.pk).update(total_points=F("total_points"))
    user_team = get_user_team(user)

    # چک دسترسی: ماموریت باید برای تیم کاربر فعال باشد یا سراسری باشد
    if not mission.is_global:
        if not user_team or not mission.team_assignments.filter(
            team=user_team, is_active=True
        ).exists():
            raise MissionTeamAccessDenied('این ماموریت برای تیم شما فعال نیست.')

    if not mission.is_available_now():
        raise SubmissionRejected('این ماموریت در این ساعت قابل انجام نیست.')

    if has_completed_today(user, mission):
        raise SubmissionRejected('شما امروز این ماموریت را انجام داده\u200cاید.')

    if has_pending_request_today(user, mission):
        raise SubmissionRejected('شما امروز برای این ماموریت درخواست ثبت کرده\u200cاید.')

    note = note.strip()
    mr = MissionRequest.objects.create(
        user=user,
        mission=mission,
        team=user_team,
        note=note or None,
        status='pending',
    )
    return mr
