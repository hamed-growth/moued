def dashboard_badges(request):
    """
    تعداد آیتم‌های در انتظار (برای نمایش badge روی منو).
    """
    if not request.user.is_authenticated:
        return {}
    if not (request.user.is_staff or request.user.is_superuser):
        return {}

    from missions.models import MissionRequest, TreasurePurchase

    return {
        'dash_pending_requests': MissionRequest.objects.filter(status='pending').count(),
        'dash_pending_purchases': TreasurePurchase.objects.filter(status='pending').count(),
    }