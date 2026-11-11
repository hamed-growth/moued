from apps.backoffice.selectors.overview import get_dashboard_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta
import logging

from missions.models import (
    User, Team, TeamMember, PointTransaction,
    MissionCategory, Mission, TeamMission, MissionCompletion, MissionRequest,
    Competition, CompetitionRegistration,
    Question, DailyQuestion, DailyQuestionAnswer,
    TreasureCategory, TreasureItem, TreasurePurchase,
)
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

    users = User.objects.all().order_by('-total_points')

    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q)
        )

    if role == 'staff':
        users = users.filter(is_staff=True)
    elif role == 'manager':
        users = users.filter(is_team_manager=True)
    elif role == 'inactive':
        users = users.filter(is_active=False)

    if team_id:
        users = users.filter(team_membership__team_id=team_id)

    users = users.select_related('team_membership__team')

    teams = Team.objects.all().order_by('name')

    context = {
        'users': users[:200],
        'teams': teams,
        'q': q,
        'role': role,
        'team_id': team_id,
    }
    return render(request, 'dashboard/users.html', context)


@staff_required
def user_detail(request, user_id):
    """پروفایل کاربر از دید مدیر"""
    user = get_object_or_404(User, id=user_id)

    transactions = PointTransaction.objects.filter(user=user).order_by('-created_at')[:50]
    completions = MissionCompletion.objects.filter(user=user).select_related('mission', 'team').order_by('-completed_at')[:20]
    requests = MissionRequest.objects.filter(user=user).select_related('mission', 'team').order_by('-requested_at')[:20]
    competitions = CompetitionRegistration.objects.filter(user=user).select_related('competition').order_by('-registered_at')[:20]

    user_team = None
    try:
        user_team = user.team_membership.team
    except TeamMember.DoesNotExist:
        pass

    context = {
        'target_user': user,
        'transactions': transactions,
        'completions': completions,
        'requests': requests,
        'competitions': competitions,
        'user_team': user_team,
    }
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
    user.is_staff = not user.is_staff
    user.save(update_fields=['is_staff'])
    messages.success(
        request,
        f'دسترسی کارمندی «{user.username}» {"فعال" if user.is_staff else "غیرفعال"} شد.'
    )
    return redirect('dashboard:user_detail', user_id=user.id)


@staff_required
@require_POST
def user_toggle_manager(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_team_manager = not user.is_team_manager
    user.save(update_fields=['is_team_manager'])
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
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
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
    teams = Team.objects.select_related('manager').annotate(
        members_count=Count('members', distinct=True),
        total_points_sum=Sum('members__user__total_points'),
    ).order_by('-total_points_sum')

    context = {'teams': teams}
    return render(request, 'dashboard/teams.html', context)


@staff_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    members = (
        TeamMember.objects
        .filter(team=team)
        .select_related('user')
        .order_by('-user__total_points')
    )

    # ماموریت‌های موجود و وضعیت فعال‌سازی برای این تیم
    missions = Mission.objects.filter(is_active=True).select_related('category').order_by('title')
    active_team_mission_ids = set(
        TeamMission.objects.filter(team=team, is_active=True).values_list('mission_id', flat=True)
    )

    context = {
        'team': team,
        'members': members,
        'missions': missions,
        'active_team_mission_ids': active_team_mission_ids,
    }
    return render(request, 'dashboard/team_detail.html', context)


@staff_required
@require_POST
def team_mission_toggle(request, team_id, mission_id):
    team = get_object_or_404(Team, id=team_id)
    mission = get_object_or_404(Mission, id=mission_id)

    if mission.is_global:
        messages.warning(request, 'این ماموریت سراسری است و نیازی به فعال‌سازی ندارد.')
        return redirect('dashboard:team_detail', team_id=team.id)

    tm, created = TeamMission.objects.get_or_create(
        team=team, mission=mission,
        defaults={'is_active': True},
    )
    if not created:
        tm.is_active = not tm.is_active
        tm.save(update_fields=['is_active'])

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
    missions = (
        Mission.objects
        .select_related('category', 'created_by')
        .annotate(
            completions_count=Count('missioncompletion', distinct=True),
            requests_count=Count('requests', distinct=True),
        )
        .order_by('-created_at')
    )

    categories = MissionCategory.objects.filter(is_active=True).order_by('order')

    context = {
        'missions': missions,
        'categories': categories,
    }
    return render(request, 'dashboard/missions.html', context)


@staff_required
def mission_requests_list(request):
    status = request.GET.get('status', 'pending')
    requests_qs = (
        MissionRequest.objects
        .select_related('user', 'mission', 'team', 'reviewed_by')
        .order_by('-requested_at')
    )
    if status in ('pending', 'approved', 'rejected'):
        requests_qs = requests_qs.filter(status=status)

    context = {
        'requests': requests_qs[:200],
        'status': status,
        'pending_count': MissionRequest.objects.filter(status='pending').count(),
    }
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
    competitions = (
        Competition.objects
        .annotate(
            registrations_count=Count('registrations', distinct=True),
            questions_count=Count('competition_questions', distinct=True),
        )
        .order_by('-start_date')
    )

    context = {'competitions': competitions}
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
    questions = Question.objects.all().order_by('-id')
    if q:
        questions = questions.filter(text__icontains=q)

    context = {
        'questions': questions[:200],
        'total': Question.objects.count(),
        'q': q,
    }
    return render(request, 'dashboard/questions.html', context)


@staff_required
def daily_questions_list(request):
    today = timezone.localdate()
    daily_qs = (
        DailyQuestion.objects
        .select_related('question')
        .annotate(answers_count=Count('answers', distinct=True))
        .order_by('-publish_date')
    )

    context = {
        'daily_questions': daily_qs[:200],
        'today': today,
        'today_count': DailyQuestion.objects.filter(publish_date=today, is_active=True).count(),
    }
    return render(request, 'dashboard/daily_questions.html', context)


# =====================================================================
# صندوق گنج
# =====================================================================

@staff_required
def treasure_list(request):
    items = (
        TreasureItem.objects
        .select_related('category')
        .annotate(purchases_count=Count('purchases', distinct=True))
        .order_by('-created_at')
    )

    purchases = (
        TreasurePurchase.objects
        .select_related('user', 'item')
        .order_by('-purchased_at')[:100]
    )

    context = {
        'items': items,
        'purchases': purchases,
        'pending_count': TreasurePurchase.objects.filter(status='pending').count(),
    }
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

    qs = PointTransaction.objects.select_related('user').order_by('-created_at')

    if ttype:
        qs = qs.filter(transaction_type=ttype)
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(title__icontains=q))

    totals = qs.aggregate(p=Sum('points'), c=Sum('coins'))

    context = {
        'transactions': qs[:300],
        'type': ttype,
        'q': q,
        'transaction_types': PointTransaction.TRANSACTION_TYPES,
        'total_points': totals['p'] or 0,
        'total_coins': totals['c'] or 0,
    }
    return render(request, 'dashboard/transactions.html', context)
