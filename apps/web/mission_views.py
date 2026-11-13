from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from apps.missions.selectors.path import day_range, path_header


@login_required(login_url='missions:home')
def missions_page(request):
    today = timezone.localdate()
    first_day = max(timezone.localtime(request.user.date_joined).date(), today - timedelta(days=3))
    days = day_range(request.user, first_day, today + timedelta(days=3))
    return render(request, 'missions/index.html', {'days': days, 'summary': path_header(request.user, days), 'today': today})


def mission_days(request):
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    before, after = request.GET.get('before'), request.GET.get('after')
    if bool(before) == bool(after):
        return HttpResponseBadRequest('یک جهت لازم است.')
    try:
        anchor = date.fromisoformat(before or after)
        count = min(max(int(request.GET.get('count', 3)), 1), 3)
    except ValueError:
        return HttpResponseBadRequest('تاریخ نامعتبر است.')
    today = timezone.localdate()
    earliest = max(timezone.localtime(request.user.date_joined).date(), today - timedelta(days=365))
    latest = today + timedelta(days=14)
    start = max(earliest, anchor - timedelta(days=count)) if before else anchor + timedelta(days=1)
    end = anchor - timedelta(days=1) if before else min(latest, anchor + timedelta(days=count))
    days = day_range(request.user, start, end) if start <= end else []
    response = render(request, 'components/mission_days.html', {'days': days})
    response['Cache-Control'] = 'no-store'
    return response
