"""Current mission visibility and daily eligibility queries."""
from django.db.models import Q
from django.utils import timezone
from missions.models import Mission, MissionCompletion, MissionRequest
from apps.teams.selectors.membership import get_user_team

def get_user_available_missions(user):
    """
    ماموریت‌های فعال برای کاربر:
    - ماموریت‌های سراسری (is_global=True)
    - ماموریت‌های فعال‌شده برای تیم کاربر
    """
    team = get_user_team(user)
    qs = Mission.objects.filter(is_active=True)

    if team:
        qs = qs.filter(
            Q(is_global=True) |
            Q(team_assignments__team=team, team_assignments__is_active=True)
        ).distinct()
    else:
        qs = qs.filter(is_global=True)

    return qs


def has_completed_today(user, mission):
    """آیا کاربر امروز این ماموریت را انجام داده؟ (ریست خودکار بعد از نیمه‌شب)"""
    today = timezone.localdate()
    return MissionCompletion.objects.filter(
        user=user, mission=mission, completed_at__date=today
    ).exists()


def has_pending_request_today(user, mission):
    """آیا کاربر امروز برای این ماموریت درخواست ثبت کرده؟ (به‌جز رد‌شده‌ها)"""
    today = timezone.localdate()
    return MissionRequest.objects.filter(
        user=user, mission=mission,
        requested_at__date=today,
    ).exclude(status='rejected').exists()

