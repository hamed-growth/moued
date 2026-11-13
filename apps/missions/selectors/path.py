"""Read model for the dated mission path. Gregorian dates stay in storage."""
from datetime import timedelta
import jdatetime
from django.db.models import Q, Sum
from django.utils import timezone
from apps.missions.models import Mission, MissionRequest, MissionCompletion
from apps.teams.selectors.membership import get_user_team

DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
WEEKDAYS = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']
MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
          'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
STATE_LABELS = {'available': 'آماده', 'not_open': 'هنوز باز نشده', 'missed': 'از دست رفت',
                'pending': 'در انتظار تأیید', 'approved': 'تأیید شده', 'rejected': 'رد شده',
                'locked': 'قفل شده'}


def get_day_missions(user, date):
    """Return the path nodes for one Gregorian day with their computed states."""
    return day_range(user, date, date)[0]['nodes']


def day_range(user, start, end):
    today = timezone.localdate()
    team = get_user_team(user)
    missions = list(Mission.objects.filter(is_active=True).filter(
        Q(is_global=True) | Q(team_assignments__team=team, team_assignments__is_active=True)
    ).select_related('category').distinct().order_by('home_order', 'pk')) if team else list(
        Mission.objects.filter(is_active=True, is_global=True).select_related('category').order_by('home_order', 'pk')
    )
    requests = MissionRequest.objects.filter(user=user, requested_at__date__range=(start, end)).order_by('requested_at', 'pk')
    completions = MissionCompletion.objects.filter(user=user, completed_at__date__range=(start, end))
    by_request = {(timezone.localtime(r.requested_at).date(), r.mission_id): r for r in requests}
    by_completion = {(timezone.localtime(c.completed_at).date(), c.mission_id) for c in completions}
    now_time = timezone.localtime().time()
    days = []
    current_found = False
    for offset in range((end - start).days + 1):
        date = start + timedelta(days=offset)
        jalali = jdatetime.date.fromgregorian(date=date)
        label = f'{WEEKDAYS[date.weekday()]} {jalali.day} {MONTHS[jalali.month - 1]}'.translate(DIGITS)
        relative = 'امروز' if date == today else 'دیروز' if date == today - timedelta(days=1) else 'فردا' if date == today + timedelta(days=1) else ''
        nodes = []
        for mission in missions:
            request = by_request.get((date, mission.pk))
            if request:
                state = request.status
            elif (date, mission.pk) in by_completion:
                state = 'approved'
            elif date > today:
                state = 'locked'
            elif date < today:
                state = 'missed'
            elif mission.has_time_limit and mission.start_time and now_time < mission.start_time:
                state = 'not_open'
            elif mission.has_time_limit and mission.end_time and now_time > mission.end_time:
                state = 'missed'
            else:
                state = 'available'
            retry_allowed = date == today and state == 'rejected' and mission.is_available_now()
            current = date == today and state == 'available' and not current_found
            current_found |= current
            nodes.append({'mission': mission, 'state': state, 'state_label': STATE_LABELS[state], 'current': current,
                          'retry_allowed': retry_allowed,
                          'time_label': f'{mission.start_time:%H:%M} تا {mission.end_time:%H:%M}'.translate(DIGITS) if mission.has_time_limit and mission.start_time and mission.end_time else 'بدون محدودیت زمانی'})
        days.append({'date': date, 'iso': date.isoformat(), 'label': label, 'relative': relative,
                     'today': date == today, 'nodes': nodes})
    return days


def path_header(user, today_days):
    today = timezone.localdate()
    requests = MissionRequest.objects.filter(user=user)
    pending = requests.filter(status='pending').aggregate(total=Sum('mission__points'))['total'] or 0
    approved_points = MissionCompletion.objects.filter(user=user).aggregate(total=Sum('points_awarded'))['total'] or 0
    active_dates = set(requests.filter(status__in=('pending', 'approved')).values_list('requested_at__date', flat=True))
    streak = 0
    streak_day = today
    if streak_day not in active_dates:
        streak_day -= timedelta(days=1)
    while streak_day in active_dates:
        streak += 1
        streak_day -= timedelta(days=1)
    completed = sum(n['state'] == 'approved' for d in today_days if d['today'] for n in d['nodes'])
    total = sum(len(d['nodes']) for d in today_days if d['today'])
    return {'points': approved_points, 'pending': pending, 'streak': streak,
            'completed': completed, 'total': total}
