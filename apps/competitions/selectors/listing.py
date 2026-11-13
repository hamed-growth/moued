"""Competition lists preserving date windows, limits and ordering."""
from django.db.models import Q
from django.utils import timezone
from apps.competitions.models import Competition, CompetitionRegistration

def get_competition_list_context(user):
    """لیست مسابقات — فعال، به‌زودی، پایان‌یافته"""
    now = timezone.now()

    active_competitions = Competition.objects.filter(
        status='active',
        start_date__lte=now,
        end_date__gte=now,
    ).order_by('end_date')

    upcoming_competitions = Competition.objects.filter(
        status__in=['upcoming', 'draft'],
        start_date__gt=now,
    ).order_by('start_date')

    finished_competitions = Competition.objects.filter(
        Q(status='finished') | Q(end_date__lt=now)
    ).order_by('-end_date')[:10]

    user_reg_ids = list(
        CompetitionRegistration.objects.filter(
            user=user
        ).values_list('competition_id', flat=True)
    )

    context = {
        'active_competitions': active_competitions,
        'upcoming_competitions': upcoming_competitions,
        'finished_competitions': finished_competitions,
        'user_reg_ids': user_reg_ids,
    }
    return context
