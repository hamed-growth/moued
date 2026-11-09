"""Read-only profile rank and activity history."""

from django.db.models import Count, Q

from ..models import CompetitionRegistration, MissionCompletion, User


def get_profile_rank(user):
    totals = User.objects.filter(is_active=True).aggregate(
        ahead=Count('pk', filter=Q(total_points__gt=user.total_points)),
        total=Count('pk'),
    )
    return totals['ahead'] + 1, totals['total']


def get_profile_history(user):
    completions = MissionCompletion.objects.filter(user=user).select_related(
        'mission', 'team',
    ).order_by('-completed_at')
    registrations = CompetitionRegistration.objects.filter(user=user).select_related(
        'competition',
    ).order_by('-registered_at')
    return completions.count(), completions[:10], registrations
