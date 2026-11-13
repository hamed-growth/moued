"""Account queries used by authorized staff."""
from django.db.models import Q

from apps.accounts.models import User
from apps.competitions.models import CompetitionRegistration
from apps.missions.models import MissionCompletion, MissionRequest
from apps.teams.models import Team, TeamMember
from apps.wallet.models import PointTransaction


def get_staff_user_detail_context(user):
    transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')[:50]
    completions = MissionCompletion.objects.filter(user=user).select_related('mission', 'team').order_by('-completed_at')[:20]
    requests = MissionRequest.objects.filter(user=user).select_related('mission', 'team').order_by('-requested_at')[:20]
    competitions = CompetitionRegistration.objects.filter(user=user).select_related('competition').order_by('-registered_at')[:20]

    user_team = None
    try:
        user_team = user.team_membership.team
    except TeamMember.DoesNotExist:
        pass

    context = {
        'target_user': user,
        'transactions': transactions,
        'completions': completions,
        'requests': requests,
        'competitions': competitions,
        'user_team': user_team,
    }
    return context


def get_staff_user_list_context(q, role, team_id):
    users = User.objects.all().order_by('-total_points')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )

    if role == 'staff':
        users = users.filter(is_staff=True)
    elif role == 'manager':
        users = users.filter(is_team_manager=True)
    elif role == 'inactive':
        users = users.filter(is_active=False)

    if team_id:
        users = users.filter(team_membership__team_id=team_id)

    users = users.select_related('team_membership__team')

    teams = Team.objects.all().order_by('name')

    context = {
        'users': users[:200],
        'teams': teams,
        'q': q,
        'role': role,
        'team_id': team_id,
    }
    return context
