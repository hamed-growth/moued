from apps.accounts.services.roles import toggle_active, toggle_staff, toggle_team_manager
from apps.missions.services.team_assignment import toggle_team_assignment
from apps.missions.selectors.staff import get_staff_missions_list_context
from apps.missions.selectors.staff import get_staff_mission_requests_list_context
from apps.competitions.selectors.staff import get_staff_competitions_list_context
from apps.questions.selectors.staff import get_staff_questions_list_context
from apps.questions.selectors.staff import get_staff_daily_questions_list_context
from apps.treasure.selectors.staff import get_staff_treasure_list_context
from apps.wallet.selectors.staff import get_staff_transactions_list_context
from apps.accounts.selectors.staff import (
    get_staff_user_detail_context, get_staff_user_list_context,
)
from apps.teams.selectors.staff import get_staff_team_list_context, get_staff_team_detail_context
from apps.backoffice.selectors.overview import get_dashboard_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.http import HttpResponse
from django.views.decorators.http import require_POST
import logging

from missions.models import Competition, Mission, MissionRequest, Team, TreasurePurchase, User
from .decorators import staff_required

logger = logging.getLogger(__name__)


# =====================================================================
# خانه داشبورد
# =====================================================================

@staff_required
def home(request):
    context = get_dashboard_context()
    return render(request, 'dashboard/home.html', context)


# =====================================================================
# کاربران
# =====================================================================

@staff_required
def users_list(request):
    """لیست کاربران با جستجو و فیلتر"""
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    team_id = request.GET.get('team', '')

    context = get_staff_user_list_context(q, role, team_id)
    return render(request, 'dashboard/users.html', context)


@staff_required
def user_detail(request, user_id):
    """پروفایل کاربر از دید مدیر"""
    user = get_object_or_404(User, id=user_id)

    context = get_staff_user_detail_context(user)
    return render(request, 'dashboard/user_detail.html', context)


@staff_required
@require_POST
def user_toggle_staff(request, user_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'نمی‌توانید وضعیت خودتان را تغییر دهید.')
        return redirect('dashboard:user_detail', user_id=user.id)
    toggle_staff(user)
    messages.success(
        request,
        f'دسترسی کارمندی «{user.username}» {"فعال" if user.is_staff else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


@staff_required
@require_POST
def user_toggle_manager(request, user_id):
    user = get_object_or_404(User, id=user_id)
    toggle_team_manager(user)
    messages.success(
        request,
        f'وضعیت مدیریت تیم «{user.username}» {"فعال" if user.is_team_manager else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


@staff_required
@require_POST
def user_toggle_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'نمی‌توانید حساب خودتان را غیرفعال کنید.')
        return redirect('dashboard:user_detail', user_id=user.id)
    toggle_active(user)
    messages.success(
        request,
        f'حساب «{user.username}» {"فعال" if user.is_active else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


# =====================================================================
# تیم‌ها
# =====================================================================

@staff_required
def teams_list(request):
    context = get_staff_team_list_context()
    return render(request, 'dashboard/teams.html', context)


@staff_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    context = get_staff_team_detail_context(team)
    return render(request, 'dashboard/team_detail.html', context)


@staff_required
@require_POST
def team_mission_toggle(request, team_id, mission_id):
    team = get_object_or_404(Team, id=team_id)
    mission = get_object_or_404(Mission, id=mission_id)

    tm = toggle_team_assignment(team, mission)
    if tm is None:
        messages.warning(request, 'این ماموریت سراسری است و نیازی به فعال‌سازی ندارد.')
        return redirect('dashboard:team_detail', team_id=team.id)

    messages.success(
        request,
        f'ماموریت «{mission.title}» برای تیم «{team.name}» '
        f'{"فعال" if tm.is_active else "غیرفعال"} شد.'
    )
    return redirect('dashboard:team_detail', team_id=team.id)


# =====================================================================
# ماموریت‌ها
# =====================================================================

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


# =====================================================================
# مسابقات
# =====================================================================

@staff_required
def competitions_list(request):
    context = get_staff_competitions_list_context()
    return render(request, 'dashboard/competitions.html', context)


@staff_required
@require_POST
def competition_finalize(request, comp_id):
    comp = get_object_or_404(Competition, id=comp_id)
    try:
        finalized = comp.finalize()
    except DatabaseError:
        logger.exception("Competition finalization database operation failed")
        return HttpResponse('پایان مسابقه ثبت نشد. لطفاً دوباره تلاش کنید.', status=503)
    if finalized:
        messages.success(request, f'مسابقه «{comp.title}» پایان یافت و جوایز اهدا شد.')
    else:
        messages.info(request, 'این مسابقه قبلاً پایان یافته است.')
    return redirect('dashboard:competitions')


# =====================================================================
# سوالات
# =====================================================================

@staff_required
def questions_list(request):
    q = request.GET.get('q', '').strip()
    context = get_staff_questions_list_context(q)
    return render(request, 'dashboard/questions.html', context)


@staff_required
def daily_questions_list(request):
    context = get_staff_daily_questions_list_context()
    return render(request, 'dashboard/daily_questions.html', context)


# =====================================================================
# صندوق گنج
# =====================================================================

@staff_required
def treasure_list(request):
    context = get_staff_treasure_list_context()
    return render(request, 'dashboard/treasure.html', context)


@staff_required
@require_POST
def treasure_purchase_deliver(request, purchase_id):
    purchase = get_object_or_404(TreasurePurchase, id=purchase_id)
    note = request.POST.get('admin_note', '').strip()
    if purchase.deliver(admin_note=note or None):
        messages.success(request, f'خرید «{purchase.item_name}» تحویل شد.')
    else:
        messages.info(request, 'این خرید قبلاً تحویل داده شده است.')
    return redirect('dashboard:treasure')


# =====================================================================
# تراکنش‌ها
# =====================================================================

@staff_required
def transactions_list(request):
    ttype = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    context = get_staff_transactions_list_context(ttype, q)
    return render(request, 'dashboard/transactions.html', context)
