"""Report queries for authorized dashboard staff."""
from django.db.models import Count

from missions.models import Competition


def get_staff_competitions_list_context():
    competitions = (
        Competition.objects
        .annotate(
            registrations_count=Count('registrations', distinct=True),
            questions_count=Count('competition_questions', distinct=True),
        )
        .order_by('-start_date')
    )

    context = {'competitions': competitions}
    return context
