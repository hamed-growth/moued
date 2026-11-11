from apps.backoffice.selectors.archive import get_archive_context
from apps.competitions.selectors.detail import get_competition_detail_context
from apps.submissions import MissionTeamAccessDenied, SubmissionRejected
from apps.competitions.services.participation import (
    prepare_competition_play, register_participant, start_participation, submit_competition_answer,
)
from apps.questions.services.answers import submit_daily_answer
from apps.missions.services.requests import create_mission_request
from apps.treasure.selectors.storefront import get_storefront_context
from apps.missions.selectors.home import get_home_context
from apps.competitions.selectors.listing import get_competition_list_context
from apps.questions.selectors.daily import get_daily_question_context
from apps.teams.selectors.overview import get_league_context
from apps.accounts.selectors.overview import get_profile_context
from common.calendar import PERSIAN_MONTHS, get_persian_month_name, get_shamsi_month_range
from apps.wallet.selectors.history import get_user_months_shamsi
from apps.teams.selectors.membership import get_user_team
from apps.missions.selectors.eligibility import (
    get_user_available_missions, has_completed_today, has_pending_request_today,
)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
from django.utils import timezone
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
import logging

from .forms import UserRegisterForm, UserLoginForm
from .models import (
    Mission,
    Competition,
    CompetitionQuestion,
    CompetitionRegistration,
    DailyQuestion,
    TreasureItem,
)
from apps.teams.selectors.leagues import get_league_rankings, get_profile_team_leaderboard
from apps.accounts.selectors.profiles import get_profile_history, get_profile_rank
from apps.treasure.services.checkout import InsufficientPoints, OutOfStock, purchase_treasure_item

logger = logging.getLogger(__name__)


# =====================================================================
# صفحات عمومی
# =====================================================================

def home(request):
    context = get_home_context(request.user)
    return render(request, 'missions/home.html', context)


# =====================================================================
# احراز هویت
# =====================================================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('missions:home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد. خوش آمدید!')
            return redirect('missions:home')
    else:
        form = UserRegisterForm()

    return render(request, 'missions/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('missions:home')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'خوش آمدید {user.username}!')
            next_url = request.GET.get('next', 'missions:home')
            return redirect(next_url)
    else:
        form = UserLoginForm()

    return render(request, 'missions/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'با موفقیت خارج شدید.')
    return redirect('missions:home')


# =====================================================================
# ماموریت‌ها
# =====================================================================

def submission_error_response(error):
    data = {'success': False, 'message': str(error)}
    if error.completed:
        data['is_completed'] = True
    return JsonResponse(data, status=400)


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


# =====================================================================
# مسابقات (یکپارچه — Competition)
# =====================================================================

@login_required
def competition_list(request):
    context = get_competition_list_context(request.user)
    return render(request, 'missions/competition_list.html', context)


@login_required
def competition_detail(request, competition_id):
    """صفحه شروع/اطلاعات مسابقه"""
    competition = get_object_or_404(Competition, id=competition_id)

    context = get_competition_detail_context(competition, request.user)
    return render(request, 'missions/competition_detail.html', context)


@login_required
def competition_play(request, competition_id):
    """صفحه بازی مسابقه — شبیه سوالات روزانه"""
    competition = get_object_or_404(Competition, id=competition_id)

    outcome, context = prepare_competition_play(request.user, competition)
    if outcome:
        if outcome == 'unavailable':
            starts_at = competition.start_date.strftime("%Y/%m/%d — %H:%M")
            messages.warning(request, f'این مسابقه از تاریخ {starts_at} شروع می‌شود.')
        else:
            level, message = {
                'finished': (messages.ERROR, 'این مسابقه به پایان رسیده است.'),
                'unregistered': (messages.WARNING, 'ابتدا در مسابقه ثبت‌نام کنید.'),
                'completed': (messages.INFO, 'شما این مسابقه را به پایان رسانده‌اید.'),
                'expired': (messages.WARNING, 'زمان مسابقه شما به پایان رسیده است.'),
                'exhausted': (messages.INFO, 'شما به همه سوالات این مسابقه پاسخ داده‌اید.'),
            }[outcome]
            messages.add_message(request, level, message)
        return redirect('missions:competition_detail', competition_id=competition.id)

    return render(request, 'missions/competition_play.html', context)


@login_required
@require_POST
def start_competition(request, competition_id):
    """شروع رسمی مسابقه — ثبت started_at"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        registration = start_participation(request.user, competition)
    except SubmissionRejected as exc:
        return submission_error_response(exc)

    return JsonResponse({
        'success': True,
        'started_at': registration.started_at.isoformat(),
        'time_limit_minutes': competition.time_limit_minutes,
    })


@login_required
@require_POST
def register_competition(request, competition_id):
    """ثبت‌نام در مسابقه — حتی قبل از شروع"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        created = register_participant(request.user, competition)
    except SubmissionRejected as exc:
        messages.error(request, str(exc))
        return redirect('missions:competition_detail', competition_id=competition.id)

    if created:
        messages.success(
            request,
            f'در مسابقه «{competition.title}» ثبت‌نام شدید. '
            f'از تاریخ شروع می‌توانید بازی کنید.'
        )
    else:
        messages.info(request, 'قبلاً در این مسابقه ثبت‌نام کرده‌اید.')

    return redirect('missions:competition_detail', competition_id=competition.id)


@login_required
@require_POST
def submit_answer(request, competition_id, question_id):
    """ثبت پاسخ به سوال مسابقه — با کنترل زمان و محدودیت تعداد"""
    competition = get_object_or_404(Competition, id=competition_id)

    try:
        answer, registration = submit_competition_answer(request.user, competition, question_id, request.POST.get('option', 0))
    except CompetitionQuestion.DoesNotExist as exc:
        raise Http404('No CompetitionQuestion matches the given query.') from exc
    except SubmissionRejected as exc:
        return submission_error_response(exc)

    return JsonResponse({
        'success': True,
        'is_correct': answer.is_correct,
        'correct_option': answer.question.correct_option,
        'total_correct': registration.total_correct,
        'total_answered': registration.total_answered,
        'score': registration.score,
        'is_completed': registration.is_completed,
    })


@login_required
@require_POST
def finish_competition(request, competition_id):
    """پایان دستی مسابقه توسط کاربر"""
    competition = get_object_or_404(Competition, id=competition_id)
    registration = get_object_or_404(
        CompetitionRegistration,
        user=request.user,
        competition=competition
    )

    if not registration.finish():
        return JsonResponse({
            'success': False,
            'message': 'مسابقه قبلاً به پایان رسیده است.'
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': 'مسابقه شما به پایان رسید و امتیازات ثبت شد.',
        'score': registration.score,
        'total_correct': registration.total_correct,
    })


# =====================================================================
# پروفایل
# =====================================================================

@login_required
def profile(request):
    context = get_profile_context(request.user, request.GET.get('month', ''))
    return render(request, 'missions/profile.html', context)


# =====================================================================
# آرشیو
# =====================================================================

@login_required
def archive(request):
    context = get_archive_context()
    return render(request, 'missions/archive.html', context)


# =====================================================================
# لیگ‌ها (گروه‌ها)
# =====================================================================

@login_required
def league_list(request):
    context = get_league_context(request.user, request.GET.get('month', ''))
    return render(request, 'missions/league_list.html', context)


# =====================================================================
# سوالات روزانه
# =====================================================================

@login_required
def daily_questions_page(request):
    context = get_daily_question_context(request.user)
    return render(request, 'missions/daily_questions.html', context)


@login_required
@require_POST
def answer_daily(request, dq_id):
    dq = get_object_or_404(DailyQuestion, id=dq_id, is_active=True)

    try:
        answer = submit_daily_answer(request.user, dq, request.POST.get('option', 0))
    except SubmissionRejected as exc:
        return submission_error_response(exc)

    return JsonResponse({
        'success': True,
        'is_correct': answer.is_correct,
        'correct_option': dq.question.correct_option,
        'points': answer.points_awarded,
        'new_total': request.user.total_points,
    })


# =====================================================================
# صندوق گنج (فروشگاه امتیازی)
# =====================================================================

@login_required
def treasure_box(request):
    context = get_storefront_context(request.user, request.GET.get('category', ''))
    return render(request, 'missions/treasure_box.html', context)


@login_required
@require_POST
def buy_treasure_item(request, item_id):
    """خرید آیتم از فروشگاه صندوق گنج"""
    try:
        purchase, new_total = purchase_treasure_item(request.user, item_id)
    except TreasureItem.DoesNotExist as exc:
        raise Http404('No TreasureItem matches the given query.') from exc
    except OutOfStock:
        return JsonResponse({
            'success': False,
            'message': 'این آیتم موجود نیست.'
        }, status=400)
    except InsufficientPoints as exc:
        return JsonResponse({
            'success': False,
            'message': f'امتیاز کافی ندارید. {exc.shortfall} امتیاز دیگر لازم دارید.'
        }, status=400)
    except DatabaseError:
        logger.exception("Treasure purchase database operation failed")
        return JsonResponse({
            'success': False,
            'message': 'خرید انجام نشد. لطفاً دوباره تلاش کنید.'
        }, status=503)

    return JsonResponse({
        'success': True,
        'message': f'آیتم «{purchase.item_name}» با موفقیت خریداری شد! در انتظار تحویل.',
        'new_total': new_total,
        'purchase_id': purchase.id,
    })
