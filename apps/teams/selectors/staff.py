"""Team read models for authorized staff; HTTP access checks stay in dashboard."""
from django.db.models import Count, Sum
from missions.models import Team, TeamMember, Mission, TeamMission


def get_staff_team_list_context():
    teams = Team.objects.select_related('manager').annotate(
        members_count=Count('members', distinct=True),
        total_points_sum=Sum('members__user__total_points'),
    ).order_by('-total_points_sum')

    context = {'teams': teams}
    return context


def get_staff_team_detail_context(team):

    members = (
        TeamMember.objects
        .filter(team=team)
        .select_related('user')
        .order_by('-user__total_points')
    )

    # ماموریت‌های موجود و وضعیت فعال‌سازی برای این تیم
    missions = Mission.objects.filter(is_active=True).select_related('category').order_by('title')
    active_team_mission_ids = set(
        TeamMission.objects.filter(team=team, is_active=True).values_list('mission_id', flat=True)
    )

    context = {
        'team': team,
        'members': members,
        'missions': missions,
        'active_team_mission_ids': active_team_mission_ids,
    }
    return context

