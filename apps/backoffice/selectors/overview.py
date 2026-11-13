"""Staff overview queries. Authorization stays in the dashboard view."""
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
import jdatetime
from common.calendar import get_shamsi_month_range
from apps.accounts.models import User
from apps.competitions.models import Competition
from apps.missions.models import Mission, MissionRequest
from apps.teams.models import Team
from apps.treasure.models import TreasurePurchase
from apps.wallet.models import PointTransaction

def get_dashboard_context():
    """صفحه اصلی داشبورد — آمار کلی"""
    now = timezone.now()
    today = timezone.localdate()
    week_ago = now - timedelta(days=7)

    stats = {
        'users_count': User.objects.filter(is_active=True).count(),
        'staff_count': User.objects.filter(is_staff=True).count(),
        'teams_count': Team.objects.count(),
        'missions_count': Mission.objects.filter(is_active=True).count(),
        'competitions_active': Competition.objects.filter(
            status='active', end_date__gte=now
        ).count(),
        'pending_requests': MissionRequest.objects.filter(status='pending').count(),
        'pending_purchases': TreasurePurchase.objects.filter(status='pending').count(),
        'total_points_awarded': PointTransaction.objects.aggregate(
            s=Sum('points')
        )['s'] or 0,
        'total_coins_awarded': PointTransaction.objects.aggregate(
            s=Sum('coins')
        )['s'] or 0,
        'week_transactions': PointTransaction.objects.filter(
            created_at__gte=week_ago
        ).count(),
    }

    # ۱۰ کاربر برتر
    jalali_today = jdatetime.date.fromgregorian(date=today)
    month_start, month_end, _ = get_shamsi_month_range(f'{jalali_today.year}-{jalali_today.month:02d}')
    from django.db.models import Q
    top_users = User.objects.filter(is_active=True).annotate(
        month_points=Sum('transactions__points', filter=Q(
            transactions__created_at__gte=month_start,
            transactions__created_at__lt=month_end,
        )),
    ).order_by('-month_points', 'pk')[:10]

    # آخرین درخواست‌های در انتظار
    pending_requests = (
        MissionRequest.objects
        .filter(status='pending')
        .select_related('user', 'mission', 'team')
        .order_by('-requested_at')[:8]
    )

    # آخرین خریدهای در انتظار
    pending_purchases = (
        TreasurePurchase.objects
        .filter(status='pending')
        .select_related('user', 'item')
        .order_by('-purchased_at')[:8]
    )

    # آمار ۷ روز اخیر (برای نمودار ساده)
    week_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = PointTransaction.objects.filter(
            created_at__date=d
        ).count()
        week_days.append({'date': d, 'count': count})

    context = {
        'stats': stats,
        'top_users': top_users,
        'pending_requests': pending_requests,
        'pending_purchases': pending_purchases,
        'week_days': week_days,
    }
    return context
