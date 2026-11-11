"""Report queries for authorized dashboard staff."""
from django.db.models import Count
from django.utils import timezone

from missions.models import DailyQuestion, Question


def get_staff_questions_list_context(q):
    questions = Question.objects.all().order_by('-id')
    if q:
        questions = questions.filter(text__icontains=q)

    context = {
        'questions': questions[:200],
        'total': Question.objects.count(),
        'q': q,
    }
    return context


def get_staff_daily_questions_list_context():
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
    return context
