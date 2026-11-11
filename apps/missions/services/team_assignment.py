from missions.models import TeamMission


def toggle_team_assignment(team, mission):
    if mission.is_global:
        return None
    tm, created = TeamMission.objects.get_or_create(
        team=team, mission=mission,
        defaults={'is_active': True},
    )
    if not created:
        tm.is_active = not tm.is_active
        tm.save(update_fields=['is_active'])
    return tm
