"""Read-only profile rank and activity history."""

from django.db.models import Sum

from apps.wallet.models import PointTransaction
from common.calendar import get_shamsi_month_range
import jdatetime
from django.utils import timezone

from apps.accounts.models import User
from apps.competitions.models import CompetitionRegistration
from apps.missions.models import MissionCompletion


def get_profile_rank(user):
    today = jdatetime.date.fromgregorian(date=timezone.localdate())
    start, end, _ = get_shamsi_month_range(f'{today.year}-{today.month:02d}')
    monthly = dict(PointTransaction.objects.filter(
        created_at__gte=start, created_at__lt=end,
    ).values('user_id').annotate(score=Sum('points')).values_list('user_id', 'score'))
    score = monthly.get(user.pk, 0)
    active_ids = User.objects.filter(is_active=True).values_list('pk', flat=True)
    return 1 + sum(monthly.get(pk, 0) > score for pk in active_ids), len(active_ids)


def get_profile_history(user):
    completions = MissionCompletion.objects.filter(user=user).select_related(
        'mission', 'team',
    ).order_by('-completed_at')
    registrations = CompetitionRegistration.objects.filter(user=user).select_related(
        'competition',
    ).order_by('-registered_at')
    return completions.count(), completions[:10], registrations
