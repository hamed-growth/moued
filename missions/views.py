from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import DatabaseError
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.db.models.functions import TruncMonth
from datetime import datetime, time, timedelta
from collections import OrderedDict
import logging
import jdatetime

from .forms import UserRegisterForm, UserLoginForm
from .models import *
from .selectors.leagues import get_league_rankings, get_profile_team_leaderboard
from .selectors.profiles import get_profile_history, get_profile_rank
from .services.treasure import InsufficientPoints, OutOfStock, purchase_treasure_item

logger = logging.getLogger(__name__)


# =====================================================================
# ابزارهای کمکی — ماه شمسی
# =====================================================================

PERSIAN_MONTHS = [
    'فروردین', 'اردیبهشت', 'خرداد',
    'تیر', 'مرداد', 'شهریور',
    'مهر', 'آبان', 'آذر',
    'دی', 'بهمن', 'اسفند'
]


def get_persian_month_name(month_num):
    if 1 <= month_num <= 12:
        return PERSIAN_MONTHS[month_num - 1]
    return ''


def get_user_months_shamsi(user, limit=24):
    rows = (
        PointTransaction.objects
        .filter(user=user)
        .annotate(m=TruncMonth('created_at'))
        .values('m')
        .annotate(total=Sum('points'))
        .order_by('-m')
    )

    result = OrderedDict()
    for row in rows[:limit]:
        g = row['m']
        if not g:
            continue
        try:
            g_date = g.date() if hasattr(g, 'date') else g
            j = jdatetime.date.fromgregorian(date=g_date)
            key = f"{j.year}-{j.month:02d}"
            if key not in result:
                result[key] = {
                    'value': key,
                    'year': j.year,
                    'month': j.month,
                    'label': f"{get_persian_month_name(j.month)} {j.year}",
                    'total': row['total'] or 0,
                }
            else:
                result[key]['total'] += row['total'] or 0
        except Exception:
            continue

    return list(result.values())


def get_shamsi_month_range(year_month_str):
    year, month = map(int, year_month_str.split('-'))

    start_jdate = jdatetime.date(year, month, 1)
    if month == 12:
        end_jdate = jdatetime.date(year + 1, 1, 1)
    else:
        end_jdate = jdatetime.date(year, month + 1, 1)

    start_gregorian = start_jdate.togregorian()
    end_gregorian = end_jdate.togregorian()

    start_dt = datetime.combine(start_gregorian, time.min)
    end_dt = datetime.combine(end_gregorian, time.min)

    label = f"{get_persian_month_name(start_jdate.month)} {year}"

    return start_dt, end_dt, label


# =====================================================================
# ابزارهای کمکی — ماموریت‌ها و ریست شبانه
# =====================================================================

def get_user_team(user):
    """تیم کاربر (یا None)"""
    try:
        return user.team_membership.team
    except (TeamMember.DoesNotExist, AttributeError):
        return None


def get_user_available_missions(user):
    """
    ماموریت‌های فعال برای کاربر:
    - ماموریت‌های سراسری (is_global=True)
    - ماموریت‌های فعال‌شده برای تیم کاربر
    """
    team = get_user_team(user)
    qs = Mission.objects.filter(is_active=True)

    if team:
        qs = qs.filter(
            Q(is_global=True) |
            Q(team_assignments__team=team, team_assignments__is_active=True)
        ).distinct()
    else:
        qs = qs.filter(is_global=True)

    return qs


def has_completed_today(user, mission):
    """آیا کاربر امروز این ماموریت را انجام داده؟ (ریست خودکار بعد از نیمه‌شب)"""
    today = timezone.localdate()
    return MissionCompletion.objects.filter(
        user=user, mission=mission, completed_at__date=today
    ).exists()


def has_pending_request_today(user, mission):
    """آیا کاربر امروز برای این ماموریت درخواست ثبت کرده؟ (به‌جز رد‌شده‌ها)"""
    today = timezone.localdate()
    return MissionRequest.objects.filter(
        user=user, mission=mission,
        requested_at__date=today,
    ).exclude(status='rejected').exists()


# =====================================================================
# صفحات عمومی
# =====================================================================

def home(request):
    """
    صفحه اصلی — ماموریت‌های منتخب + ماموریت‌های درخواست‌شده امروز کاربر.
    توجه: بعد از نیمه‌شب، به‌صورت خودکار همه ماموریت‌ها «صفر» می‌شوند
    چون فیلترها بر اساس __date=today هستند.
    """
    today = timezone.localdate()

    user_team = None
    if request.user.is_authenticated:
        user_team = get_user_team(request.user)

    # ماموریت‌های موجود برای کاربر (بر اساس تیم و ماموریت‌های سراسری)
    base_qs = Mission.objects.filter(is_active=True)
    if request.user.is_authenticated and user_team:
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

    if request.user.is_authenticated:
        completed_today_ids = list(
            MissionCompletion.objects.filter(
                user=request.user, completed_at__date=today
            ).values_list('mission_id', flat=True)
        )

        pending_request_ids = list(
            MissionRequest.objects.filter(
                user=request.user,
                status__in=['pending', 'approved'],
                requested_at__date=today,
            ).values_list('mission_id', flat=True)
        )

        answered_daily_ids = list(
            DailyQuestionAnswer.objects.filter(
                user=request.user,
                daily_question__publish_date=today,
            ).values_list('daily_question_id', flat=True)
        )

        my_requested_missions = (
            MissionRequest.objects.filter(
                user=request.user,
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
        if request.user.is_authenticated else total_daily
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
    """لیست مسابقات — فعال، به‌زودی، پایان‌یافته"""
    now = timezone.now()

    active_competitions = Competition.objects.filter(
        status='active',
        start_date__lte=now,
        end_date__gte=now,
    ).order_by('end_date')

    upcoming_competitions = Competition.objects.filter(
        status__in=['upcoming', 'draft'],
        start_date__gt=now,
    ).order_by('start_date')

    finished_competitions = Competition.objects.filter(
        Q(status='finished') | Q(end_date__lt=now)
    ).order_by('-end_date')[:10]

    user_reg_ids = list(
        CompetitionRegistration.objects.filter(
            user=request.user
        ).values_list('competition_id', flat=True)
    )

    context = {
        'active_competitions': active_competitions,
        'upcoming_competitions': upcoming_competitions,
        'finished_competitions': finished_competitions,
        'user_reg_ids': user_reg_ids,
    }
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
    user = request.user

    rank, total_users = get_profile_rank(user)

    transactions = PointTransaction.objects.filter(user=user)
    total_earned = transactions.aggregate(s=Sum('points'))['s'] or 0
    total_coins_earned = transactions.aggregate(s=Sum('coins'))['s'] or 0
    total_count = transactions.count()

    month_options = get_user_months_shamsi(user)

    selected_month = request.GET.get('month', '')
    if not selected_month and month_options:
        selected_month = month_options[0]['value']

    valid_values = [opt['value'] for opt in month_options]
    if selected_month and selected_month not in valid_values:
        selected_month = valid_values[0] if valid_values else ''

    month_total = 0
    month_coins = 0
    month_breakdown = []
    selected_month_label = ''

    if selected_month:
        start_dt, end_dt, label = get_shamsi_month_range(selected_month)
        selected_month_label = label

        month_qs = transactions.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        )

        agg = month_qs.aggregate(
            p=Sum('points'),
            c=Sum('coins'),
        )
        month_total = agg['p'] or 0
        month_coins = agg['c'] or 0

        by_type = month_qs.values('transaction_type').annotate(
            total=Sum('points'),
            total_coins=Sum('coins'),
            count=Count('id'),
        ).order_by('-total')

        type_labels = dict(PointTransaction.TRANSACTION_TYPES)
        for row in by_type:
            month_breakdown.append({
                'code': row['transaction_type'],
                'label': type_labels.get(row['transaction_type'], row['transaction_type']),
                'total': row['total'] or 0,
                'total_coins': row['total_coins'] or 0,
                'count': row['count'],
            })

    pending_requests = MissionRequest.objects.filter(
        user=user, status='pending'
    ).select_related('mission')
    # مجموع پاداش‌های در انتظار (با در نظر گرفتن override تیمی)
    pending_points = 0
    pending_coins = 0
    for r in pending_requests:
        p, c = r.mission.get_rewards_for_team(r.team)
        pending_points += p
        pending_coins += c
    pending_count = pending_requests.count()

    completions_count, completions_10, registrations = get_profile_history(user)

    team_leaderboard = []
    user_team = get_user_team(user)

    if selected_month:
        start_dt, end_dt, label = get_shamsi_month_range(selected_month)

        user_month_points = {
            row['user']: row['total']
            for row in PointTransaction.objects.filter(
                created_at__gte=start_dt, created_at__lt=end_dt
            ).values('user').annotate(total=Sum('points'))
        }

        team_leaderboard = get_profile_team_leaderboard(user_month_points, user_team)

    context = {
        'rank': rank,
        'total_users': total_users,
        'total_earned': total_earned,
        'total_coins_earned': total_coins_earned,
        'total_count': total_count,
        'pending_points': pending_points,
        'pending_coins': pending_coins,
        'pending_count': pending_count,
        'completions_count': completions_count,
        'month_options': month_options,
        'selected_month': selected_month,
        'selected_month_label': selected_month_label,
        'month_total': month_total,
        'month_coins': month_coins,
        'month_breakdown': month_breakdown,
        'month_transactions_count': sum(m['count'] for m in month_breakdown),
        'completions': completions_10,
        'registrations': registrations,
        'pending_requests': pending_requests[:5],
        'team_leaderboard': team_leaderboard,
        'user_team': user_team,
    }
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
    """
    صفحه لیگ‌ها با دو بخش:
    - لیگ من: تیمی که کاربر در آن عضو است
    - سایر لیگ‌ها: بقیه تیم‌ها با امتیاز ماهانه
    """
    user = request.user

    month_options = get_user_months_shamsi(user)
    selected_month = request.GET.get('month', '')

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
    return render(request, 'missions/league_list.html', context)


# =====================================================================
# سوالات روزانه
# =====================================================================

@login_required
def daily_questions_page(request):
    today = timezone.localdate()
    daily_questions = DailyQuestion.objects.filter(
        is_active=True, publish_date=today
    ).select_related('question')

    answered_ids = list(
        DailyQuestionAnswer.objects.filter(
            user=request.user, daily_question__in=daily_questions
        ).values_list('daily_question_id', flat=True)
    )

    context = {
        'daily_questions': daily_questions,
        'answered_ids': answered_ids,
    }
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
    """صفحه فروشگاه صندوق گنج"""
    user = request.user

    items = TreasureItem.objects.filter(is_active=True).select_related('category')
    categories = TreasureCategory.objects.filter(is_active=True)

    category_slug = request.GET.get('category', '')
    active_category = None
    if category_slug:
        try:
            active_category = categories.get(slug=category_slug)
            items = items.filter(category=active_category)
        except TreasureCategory.DoesNotExist:
            pass

    items = items.order_by('-is_featured', '-created_at')

    purchases = TreasurePurchase.objects.filter(
        user=user
    ).select_related('item').order_by('-purchased_at')[:20]

    total_spent = TreasurePurchase.objects.filter(
        user=user
    ).aggregate(s=Sum('item_price'))['s'] or 0
    total_bought = TreasurePurchase.objects.filter(user=user).count()

    context = {
        'items': items,
        'categories': categories,
        'active_category': active_category,
        'category_slug': category_slug,
        'purchases': purchases,
        'total_spent': total_spent,
        'total_bought': total_bought,
    }
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
