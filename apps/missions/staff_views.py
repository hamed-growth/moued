import logging
from apps.missions.selectors.staff import get_staff_missions_list_context
from apps.missions.selectors.staff import get_staff_mission_requests_list_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import DatabaseError
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.missions.models import MissionRequest
from apps.missions.models import MissionRequest
from apps.backoffice.decorators import staff_required

logger = logging.getLogger(__name__)


@staff_required
def missions_list(request):
    context = get_staff_missions_list_context()
    return render(request, 'dashboard/missions.html', context)


@staff_required
def mission_requests_list(request):
    status = request.GET.get('status', 'pending')
    context = get_staff_mission_requests_list_context(status)
    return render(request, 'dashboard/mission_requests.html', context)


@staff_required
@require_POST
def mission_request_approve(request, req_id):
    mr = get_object_or_404(MissionRequest, id=req_id)
    try:
        approved = mr.approve(admin_user=request.user)
    except DatabaseError:
        logger.exception("Mission approval database operation failed")
        return HttpResponse('بررسی درخواست انجام نشد. لطفاً دوباره تلاش کنید.', status=503)
    if approved:
        messages.success(
            request,
            f'درخواست «{mr.user.username}» برای «{mr.mission.title}» تأیید شد '
            f'({mr.points_awarded} امتیاز و {mr.coins_awarded} سکه).'
        )
    else:
        messages.info(request, 'این درخواست قبلاً بررسی شده است.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:mission_requests'))


@staff_required
@require_POST
def mission_request_reject(request, req_id):
    mr = get_object_or_404(MissionRequest, id=req_id)
    note = request.POST.get('admin_note', '').strip()
    try:
        rejected = mr.reject(admin_user=request.user, admin_note=note or None)
    except DatabaseError:
        logger.exception("Mission rejection database operation failed")
        return HttpResponse('بررسی درخواست انجام نشد. لطفاً دوباره تلاش کنید.', status=503)
    if rejected:
        messages.success(request, 'درخواست رد شد.')
    else:
        messages.info(request, 'این درخواست قبلاً بررسی شده است.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard:mission_requests'))
