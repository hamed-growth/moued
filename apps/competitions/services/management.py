"""Status changes initiated by authorized competition staff."""

from apps.competitions.models import Competition
from apps.competitions.services.rewards import finalize_competition


def _update_unfinished_status(competitions, status):
    return competitions.exclude(status='finished').update(status=status)


def save_competition_changes(competition, changed_fields):
    """Apply validated edits without restoring a stale pre-finalization status."""
    fields = set(changed_fields)
    if 'status' in fields:
        selected = Competition.objects.filter(pk=competition.pk)
        _update_unfinished_status(selected, competition.status)
        fields.remove('status')
    competition.save(update_fields=fields)
    competition.refresh_from_db(fields=['status'])


def activate_competitions(competitions):
    return _update_unfinished_status(competitions, 'active')


def finalize_competitions(competitions):
    return sum(finalize_competition(competition) for competition in competitions)

