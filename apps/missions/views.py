from apps.submissions import MissionTeamAccessDenied, SubmissionRejected
from apps.missions.services.requests import create_mission_request
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.missions.models import Mission
from apps.web.responses import submission_error_response


@login_required
@require_POST
def request_mission(request, mission_id):
    """
    ثبت درخواست انجام ماموریت.
    - ماموریت باید برای تیم کاربر فعال باشد (یا سراسری باشد).
    - بعد از نیمه‌شب، چک «امروز» به‌صورت خودکار ریست می‌شود.
    """
    mission = get_object_or_404(Mission, id=mission_id, is_active=True)
    try:
        mr = create_mission_request(request.user, mission, request.POST.get('note', ''))
    except MissionTeamAccessDenied as exc:
        return JsonResponse({'success': False, 'message': str(exc)}, status=403)
    except SubmissionRejected as exc:
        return submission_error_response(exc)

    return JsonResponse({
        'success': True,
        'message': f'درخواست شما برای «{mission.title}» ثبت شد و در انتظار تأیید مدیر است.',
        'request_id': mr.id,
        'new_total': request.user.total_points,
    })
