"""Staff overview queries. Authorization stays in the dashboard view."""
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from missions.models import (User, Team, Mission, Competition, MissionRequest,
    TreasurePurchase, PointTransaction)

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
    top_users = User.objects.filter(is_active=True).order_by('-total_points')[:10]

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
