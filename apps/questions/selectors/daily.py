"""Today's active questions and the current user's answered IDs."""
from django.utils import timezone
from missions.models import DailyQuestion, DailyQuestionAnswer

def get_daily_question_context(user):
    today = timezone.localdate()
    daily_questions = DailyQuestion.objects.filter(
        is_active=True, publish_date=today
    ).select_related('question')

    answered_ids = list(
        DailyQuestionAnswer.objects.filter(
            user=user, daily_question__in=daily_questions
        ).values_list('daily_question_id', flat=True)
    )

    context = {
        'daily_questions': daily_questions,
        'answered_ids': answered_ids,
    }
    return context
