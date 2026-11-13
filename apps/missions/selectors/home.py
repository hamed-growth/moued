"""Homepage mission and daily-question read model, including anonymous visibility."""
from django.db.models import Q
from django.utils import timezone
from apps.missions.models import Mission, MissionCompletion, MissionRequest
from apps.questions.models import DailyQuestion, DailyQuestionAnswer
from apps.teams.selectors.membership import get_user_team

def get_home_context(user):
    """
    صفحه اصلی — ماموریت‌های منتخب + ماموریت‌های درخواست‌شده امروز کاربر.
    توجه: بعد از نیمه‌شب، به‌صورت خودکار همه ماموریت‌ها «صفر» می‌شوند
    چون فیلترها بر اساس __date=today هستند.
    """
    today = timezone.localdate()

    user_team = None
    if user.is_authenticated:
        user_team = get_user_team(user)

    # ماموریت‌های موجود برای کاربر (بر اساس تیم و ماموریت‌های سراسری)
    base_qs = Mission.objects.filter(is_active=True)
    if user.is_authenticated and user_team:
        base_qs = base_qs.filter(
            Q(is_global=True) |
            Q(team_assignments__team=user_team, team_assignments__is_active=True)
        ).distinct()
    else:
        base_qs = base_qs.filter(is_global=True)

    active_missions = base_qs.filter(show_on_home=True).order_by(
        'home_order', '-created_at'
    )
    all_missions = base_qs.order_by('title')

    completed_today_ids = []
    pending_request_ids = []
    answered_daily_ids = []
    my_requested_missions = []
    requested_mission_ids = []

    if user.is_authenticated:
        completed_today_ids = list(
            MissionCompletion.objects.filter(
                user=user, completed_at__date=today
            ).values_list('mission_id', flat=True)
        )

        pending_request_ids = list(
            MissionRequest.objects.filter(
                user=user,
                status__in=['pending', 'approved'],
                requested_at__date=today,
            ).values_list('mission_id', flat=True)
        )

        answered_daily_ids = list(
            DailyQuestionAnswer.objects.filter(
                user=user,
                daily_question__publish_date=today,
            ).values_list('daily_question_id', flat=True)
        )

        my_requested_missions = (
            MissionRequest.objects.filter(
                user=user,
                requested_at__date=today,
            )
            .select_related('mission')
            .order_by('-requested_at')
        )
        requested_mission_ids = [mr.mission_id for mr in my_requested_missions]

    active_missions = active_missions.exclude(id__in=requested_mission_ids)

    daily_questions = DailyQuestion.objects.filter(
        is_active=True, publish_date=today
    )
    total_daily = daily_questions.count()
    unanswered_daily = (
        max(0, total_daily - len(answered_daily_ids))
        if user.is_authenticated else total_daily
    )

    context = {
        'active_missions': active_missions,
        'all_missions': all_missions,
        'completed_today_ids': completed_today_ids,
        'pending_request_ids': pending_request_ids,
        'my_requested_missions': my_requested_missions,
        'total_daily': total_daily,
        'unanswered_daily': unanswered_daily,
        'user_team': user_team,
    }
    return context
