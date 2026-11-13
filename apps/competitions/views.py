from apps.competitions.selectors.detail import get_competition_detail_context
from apps.submissions import SubmissionRejected
from apps.competitions.services.participation import prepare_competition_play, register_participant, start_participation, submit_competition_answer
from apps.competitions.selectors.listing import get_competition_list_context
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST
from apps.competitions.models import Competition, CompetitionQuestion, CompetitionRegistration
from apps.web.responses import submission_error_response


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
