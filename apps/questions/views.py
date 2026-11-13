from apps.submissions import SubmissionRejected
from apps.questions.services.answers import submit_daily_answer
from apps.questions.selectors.daily import get_daily_question_context
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.questions.models import DailyQuestion
from apps.web.responses import submission_error_response


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
