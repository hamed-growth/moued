"""Report queries for authorized dashboard staff."""
from django.db.models import Count

from missions.models import Mission, MissionCategory, MissionRequest


def get_staff_missions_list_context():
    missions = (
        Mission.objects
        .select_related('category', 'created_by')
        .annotate(
            completions_count=Count('missioncompletion', distinct=True),
            requests_count=Count('requests', distinct=True),
        )
        .order_by('-created_at')
    )

    categories = MissionCategory.objects.filter(is_active=True).order_by('order')

    context = {
        'missions': missions,
        'categories': categories,
    }
    return context


def get_staff_mission_requests_list_context(status):
    requests_qs = (
        MissionRequest.objects
        .select_related('user', 'mission', 'team', 'reviewed_by')
        .order_by('-requested_at')
    )
    if status in ('pending', 'approved', 'rejected'):
        requests_qs = requests_qs.filter(status=status)

    context = {
        'requests': requests_qs[:200],
        'status': status,
        'pending_count': MissionRequest.objects.filter(status='pending').count(),
    }
    return context
