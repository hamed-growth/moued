from apps.backoffice.selectors.badges import get_staff_badges


def dashboard_badges(request):
    """
    تعداد آیتم‌های در انتظار (برای نمایش badge روی منو).
    """
    if not request.user.is_authenticated:
        return {}
    if not (request.user.is_staff or request.user.is_superuser):
        return {}

    return get_staff_badges()
