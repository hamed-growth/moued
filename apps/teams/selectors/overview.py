"""Monthly league read model with the existing month fallback policy."""
import jdatetime
from django.utils import timezone
from django.db.models import Sum
from apps.wallet.models import PointTransaction
from .membership import get_user_team
from .leagues import get_league_rankings
from apps.wallet.selectors.history import get_user_months_shamsi
from common.calendar import get_shamsi_month_range

def get_league_context(user, selected_month=""):
    """
    صفحه لیگ‌ها با دو بخش:
    - لیگ من: تیمی که کاربر در آن عضو است
    - سایر لیگ‌ها: بقیه تیم‌ها با امتیاز ماهانه
    """

    month_options = get_user_months_shamsi(user)

    if not selected_month:
        if month_options:
            selected_month = month_options[0]['value']
        else:
            today_j = jdatetime.date.fromgregorian(date=timezone.localdate())
            selected_month = f"{today_j.year}-{today_j.month:02d}"

    valid_values = [opt['value'] for opt in month_options]
    if selected_month not in valid_values:
        try:
            get_shamsi_month_range(selected_month)
        except Exception:
            if month_options:
                selected_month = month_options[0]['value']
            else:
                today_j = jdatetime.date.fromgregorian(date=timezone.localdate())
                selected_month = f"{today_j.year}-{today_j.month:02d}"

    start_dt, end_dt, label = get_shamsi_month_range(selected_month)

    user_month_points = {}
    for row in PointTransaction.objects.filter(
        created_at__gte=start_dt,
        created_at__lt=end_dt,
    ).values('user').annotate(total=Sum('points')):
        user_month_points[row['user']] = row['total'] or 0

    user_team = get_user_team(user)

    my_team_data, all_teams = get_league_rankings(user, user_team, user_month_points)

    context = {
        'selected_month': selected_month,
        'selected_month_label': label,
        'month_options': month_options,
        'my_team_data': my_team_data,
        'all_teams': all_teams,
    }
    return context
