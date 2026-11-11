"""Profile read model scoped to a caller-authorized user."""
from django.db.models import Sum, Count
from missions.models import PointTransaction, MissionRequest
from .profiles import get_profile_rank, get_profile_history
from apps.teams.selectors.membership import get_user_team
from apps.teams.selectors.leagues import get_profile_team_leaderboard
from apps.wallet.selectors.history import get_user_months_shamsi
from common.calendar import get_shamsi_month_range

def get_profile_context(user, selected_month=""):

    rank, total_users = get_profile_rank(user)

    transactions = PointTransaction.objects.filter(user=user)
    total_earned = transactions.aggregate(s=Sum('points'))['s'] or 0
    total_coins_earned = transactions.aggregate(s=Sum('coins'))['s'] or 0
    total_count = transactions.count()

    month_options = get_user_months_shamsi(user)

    if not selected_month and month_options:
        selected_month = month_options[0]['value']

    valid_values = [opt['value'] for opt in month_options]
    if selected_month and selected_month not in valid_values:
        selected_month = valid_values[0] if valid_values else ''

    month_total = 0
    month_coins = 0
    month_breakdown = []
    selected_month_label = ''

    if selected_month:
        start_dt, end_dt, label = get_shamsi_month_range(selected_month)
        selected_month_label = label

        month_qs = transactions.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        )

        agg = month_qs.aggregate(
            p=Sum('points'),
            c=Sum('coins'),
        )
        month_total = agg['p'] or 0
        month_coins = agg['c'] or 0

        by_type = month_qs.values('transaction_type').annotate(
            total=Sum('points'),
            total_coins=Sum('coins'),
            count=Count('id'),
        ).order_by('-total')

        type_labels = dict(PointTransaction.TRANSACTION_TYPES)
        for row in by_type:
            month_breakdown.append({
                'code': row['transaction_type'],
                'label': type_labels.get(row['transaction_type'], row['transaction_type']),
                'total': row['total'] or 0,
                'total_coins': row['total_coins'] or 0,
                'count': row['count'],
            })

    pending_requests = MissionRequest.objects.filter(
        user=user, status='pending'
    ).select_related('mission')
    # مجموع پاداش‌های در انتظار (با در نظر گرفتن override تیمی)
    pending_points = 0
    pending_coins = 0
    for r in pending_requests:
        p, c = r.mission.get_rewards_for_team(r.team)
        pending_points += p
        pending_coins += c
    pending_count = pending_requests.count()

    completions_count, completions_10, registrations = get_profile_history(user)

    team_leaderboard = []
    user_team = get_user_team(user)

    if selected_month:
        start_dt, end_dt, label = get_shamsi_month_range(selected_month)

        user_month_points = {
            row['user']: row['total']
            for row in PointTransaction.objects.filter(
                created_at__gte=start_dt, created_at__lt=end_dt
            ).values('user').annotate(total=Sum('points'))
        }

        team_leaderboard = get_profile_team_leaderboard(user_month_points, user_team)

    context = {
        'rank': rank,
        'total_users': total_users,
        'total_earned': total_earned,
        'total_coins_earned': total_coins_earned,
        'total_count': total_count,
        'pending_points': pending_points,
        'pending_coins': pending_coins,
        'pending_count': pending_count,
        'completions_count': completions_count,
        'month_options': month_options,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'month_total': month_total,
        'month_coins': month_coins,
        'month_breakdown': month_breakdown,
        'month_transactions_count': sum(m['count'] for m in month_breakdown),
        'completions': completions_10,
        'registrations': registrations,
        'pending_requests': pending_requests[:5],
        'team_leaderboard': team_leaderboard,
        'user_team': user_team,
    }
    return context
