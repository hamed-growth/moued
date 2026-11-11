"""Submission workflow for the questions domain."""

from missions.models import DailyQuestionAnswer
from apps.submissions import SubmissionRejected
from django.utils import timezone


def submit_daily_answer(user, dq, raw_option):
    if dq.publish_date != timezone.localdate():
        raise SubmissionRejected('این سوال مربوط به امروز نیست.')

    if DailyQuestionAnswer.objects.filter(
        user=user, daily_question=dq
    ).exists():
        raise SubmissionRejected('شما قبلاً به این سوال پاسخ داده\u200cاید.')

    try:
        option = int(raw_option)
    except (ValueError, TypeError):
        raise SubmissionRejected('گزینه نامعتبر')

    if option not in (1, 2, 3, 4):
        raise SubmissionRejected('گزینه نامعتبر')

    answer = DailyQuestionAnswer.objects.create(
        user=user,
        daily_question=dq,
        selected_option=option,
    )
    return answer
