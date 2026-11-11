from django.utils import timezone

from missions.models import Competition, Mission


def get_archive_context():
    now = timezone.now()
    finished_missions = Mission.objects.filter(is_active=False).order_by('-created_at')[:30]
    finished_competitions = Competition.objects.filter(end_date__lt=now).order_by('-end_date')[:30]

    context = {
        'finished_missions': finished_missions,
        'finished_competitions': finished_competitions,
    }
    return context
