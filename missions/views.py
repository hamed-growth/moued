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
from datetime import timedelta
import logging

from .forms import UserRegisterForm, UserLoginForm
from .models import (
    Mission,
    MissionRequest,
    Competition,
    CompetitionQuestion,
    CompetitionRegistration,
    CompetitionAnswer,
    DailyQuestion,
    DailyQuestionAnswer,
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

@login_required
@require_POST
def request_mission(request, mission_id):
    """
    ثبت درخواست انجام ماموریت.
    - ماموریت باید برای تیم کاربر فعال باشد (یا سراسری باشد).
    - بعد از نیمه‌شب، چک «امروز» به‌صورت خودکار ریست می‌شود.
    """
    mission = get_object_or_404(Mission, id=mission_id, is_active=True)
    user_team = get_user_team(request.user)

    # چک دسترسی: ماموریت باید برای تیم کاربر فعال باشد یا سراسری باشد
    if not mission.is_global:
        if not user_team or not mission.team_assignments.filter(
            team=user_team, is_active=True
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'این ماموریت برای تیم شما فعال نیست.'
            }, status=403)

    if not mission.is_available_now():
        return JsonResponse({
            'success': False,
            'message': 'این ماموریت در این ساعت قابل انجام نیست.'
        }, status=400)

    if has_completed_today(request.user, mission):
        return JsonResponse({
            'success': False,
            'message': 'شما امروز این ماموریت را انجام داده‌اید.'
        }, status=400)

    if has_pending_request_today(request.user, mission):
        return JsonResponse({
            'success': False,
            'message': 'شما امروز برای این ماموریت درخواست ثبت کرده‌اید.'
        }, status=400)

    note = request.POST.get('note', '').strip()
    mr = MissionRequest.objects.create(
        user=request.user,
        mission=mission,
        team=user_team,
        note=note or None,
        status='pending',
    )

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

    registration = CompetitionRegistration.objects.filter(
        user=request.user,
        competition=competition
    ).first()

    competition_questions = (
        competition.competition_questions
        .select_related('question')
        .order_by('order')
    )
    total_questions = competition_questions.count()
    available_questions = min(total_questions, competition.max_questions)

    leaderboard = competition.get_leaderboard(limit=10)

    context = {
        'competition': competition,
        'registration': registration,
        'total_questions': total_questions,
        'available_questions': available_questions,
        'leaderboard': leaderboard,
        'is_open': competition.is_open(),
        'can_register': competition.can_register(),
        'can_play': competition.can_play(),
        'is_finished': competition.is_finished(),
    }
    return render(request, 'missions/competition_detail.html', context)


@login_required
def competition_play(request, competition_id):
    """صفحه بازی مسابقه — شبیه سوالات روزانه"""
    competition = get_object_or_404(Competition, id=competition_id)

    if not competition.can_play():
        if competition.is_finished():
            messages.error(request, 'این مسابقه به پایان رسیده است.')
        else:
            messages.warning(
                request,
                f'این مسابقه از تاریخ {competition.start_date.strftime("%Y/%m/%d — %H:%M")} شروع می‌شود.'
            )
        return redirect('missions:competition_detail', competition_id=competition.id)

    registration = CompetitionRegistration.objects.filter(
        user=request.user,
        competition=competition
    ).first()

    if not registration:
        messages.warning(request, 'ابتدا در مسابقه ثبت‌نام کنید.')
        return redirect('missions:competition_detail', competition_id=competition.id)

    if registration.is_completed:
        messages.info(request, 'شما این مسابقه را به پایان رسانده‌اید.')
        return redirect('missions:competition_detail', competition_id=competition.id)

    if registration.is_time_expired():
        registration.finish()
        messages.warning(request, 'زمان مسابقه شما به پایان رسیده است.')
        return redirect('missions:competition_detail', competition_id=competition.id)

    registration.start()

    all_cqs = list(
        competition.competition_questions
        .select_related('question')
        .order_by('order')
    )

    answered_qids = set(
        CompetitionAnswer.objects.filter(
            registration=registration
        ).values_list('question_id', flat=True)
    )

    remaining_cqs = [cq for cq in all_cqs if cq.question_id not in answered_qids]

    remaining_slots = max(0, competition.max_questions - registration.total_answered)
    questions_to_show = remaining_cqs[:remaining_slots]

    if not questions_to_show:
        if not registration.is_completed:
            registration.finish()
        messages.info(request, 'شما به همه سوالات این مسابقه پاسخ داده‌اید.')
        return redirect('missions:competition_detail', competition_id=competition.id)

    time_remaining = 0
    if competition.time_limit_minutes > 0 and registration.started_at:
        deadline = registration.started_at + timedelta(
            minutes=competition.time_limit_minutes
        )
        remaining = (deadline - timezone.now()).total_seconds()
        time_remaining = max(0, int(remaining))

    context = {
        'competition': competition,
        'registration': registration,
        'competition_questions': questions_to_show,
        'total_remaining': len(questions_to_show),
        'time_remaining': time_remaining,
        'initial_score': registration.score,
        'initial_correct': registration.total_correct,
        'initial_answered': registration.total_answered,
    }
    return render(request, 'missions/competition_play.html', context)


@login_required
@require_POST
def start_competition(request, competition_id):
    """شروع رسمی مسابقه — ثبت started_at"""
    competition = get_object_or_404(Competition, id=competition_id)

    if not competition.can_play():
        return JsonResponse({
            'success': False,
            'message': 'این مسابقه در حال حاضر قابل بازی نیست.'
        }, status=400)

    registration, created = CompetitionRegistration.objects.get_or_create(
        user=request.user, competition=competition
    )

    if registration.is_completed:
        return JsonResponse({
            'success': False,
            'message': 'شما قبلاً این مسابقه را تمام کرده‌اید.'
        }, status=400)

    registration.start()

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

    if not competition.can_register():
        messages.error(request, 'امکان ثبت‌نام در این مسابقه وجود ندارد.')
        return redirect('missions:competition_detail', competition_id=competition.id)

    registration, created = CompetitionRegistration.objects.get_or_create(
        user=request.user,
        competition=competition
    )

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

    if not competition.can_play():
        return JsonResponse({
            'success': False,
            'message': 'این مسابقه در حال حاضر قابل بازی نیست.'
        }, status=400)

    if not competition.is_open():
        return JsonResponse({
            'success': False,
            'message': 'این مسابقه در حال برگزاری نیست.'
        }, status=400)

    competition_question = get_object_or_404(
        CompetitionQuestion,
        competition=competition,
        question_id=question_id
    )
    question = competition_question.question

    registration = CompetitionRegistration.objects.filter(
        user=request.user,
        competition=competition
    ).first()

    if not registration:
        return JsonResponse({
            'success': False,
            'message': 'ابتدا در مسابقه ثبت‌نام کنید.'
        }, status=400)

    if registration.is_completed:
        return JsonResponse({
            'success': False,
            'message': 'شما این مسابقه را به پایان رسانده‌اید.'
        }, status=400)

    if registration.is_time_expired():
        registration.finish()
        return JsonResponse({
            'success': False,
            'message': 'زمان مجاز شما به پایان رسیده است.',
            'is_completed': True,
        }, status=400)

    registration.start()

    if registration.total_answered >= competition.max_questions:
        registration.finish()
        return JsonResponse({
            'success': False,
            'message': 'به حداکثر تعداد سوال رسیده‌اید.',
            'is_completed': True,
        }, status=400)

    if CompetitionAnswer.objects.filter(
        registration=registration, question=question
    ).exists():
        return JsonResponse({
            'success': False,
            'message': 'قبلاً به این سوال پاسخ داده‌اید.'
        }, status=400)

    try:
        selected_option = int(request.POST.get('option', 0))
    except (ValueError, TypeError):
        return JsonResponse({
            'success': False,
            'message': 'گزینه نامعتبر است.'
        }, status=400)

    if selected_option not in (1, 2, 3, 4):
        return JsonResponse({
            'success': False,
            'message': 'گزینه نامعتبر است.'
        }, status=400)

    points = competition_question.get_points()
    answer = CompetitionAnswer.objects.create(
        registration=registration,
        question=question,
        selected_option=selected_option,
        is_correct=(selected_option == question.correct_option),
        points_awarded=points if selected_option == question.correct_option else 0,
    )

    registration.add_result(answer.is_correct, answer.points_awarded)

    if registration.total_answered >= competition.max_questions:
        registration.finish()

    return JsonResponse({
        'success': True,
        'is_correct': answer.is_correct,
        'correct_option': question.correct_option,
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
    now = timezone.now()
    finished_missions = Mission.objects.filter(is_active=False).order_by('-created_at')[:30]
    finished_competitions = Competition.objects.filter(end_date__lt=now).order_by('-end_date')[:30]

    context = {
        'finished_missions': finished_missions,
        'finished_competitions': finished_competitions,
    }
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

    if dq.publish_date != timezone.localdate():
        return JsonResponse({
            'success': False,
            'message': 'این سوال مربوط به امروز نیست.'
        }, status=400)

    if DailyQuestionAnswer.objects.filter(
        user=request.user, daily_question=dq
    ).exists():
        return JsonResponse({
            'success': False,
            'message': 'شما قبلاً به این سوال پاسخ داده‌اید.'
        }, status=400)

    try:
        option = int(request.POST.get('option', 0))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'گزینه نامعتبر'}, status=400)

    if option not in (1, 2, 3, 4):
        return JsonResponse({'success': False, 'message': 'گزینه نامعتبر'}, status=400)

    answer = DailyQuestionAnswer.objects.create(
        user=request.user,
        daily_question=dq,
        selected_option=option,
    )

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
