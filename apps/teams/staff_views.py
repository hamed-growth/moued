from apps.missions.services.team_assignment import toggle_team_assignment
from apps.teams.selectors.staff import get_staff_team_list_context, get_staff_team_detail_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.missions.models import Mission
from apps.teams.models import Team
from apps.missions.models import Mission
from apps.teams.models import Team
from apps.backoffice.decorators import staff_required


@staff_required
def teams_list(request):
    context = get_staff_team_list_context()
    return render(request, 'dashboard/teams.html', context)


@staff_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    context = get_staff_team_detail_context(team)
    return render(request, 'dashboard/team_detail.html', context)


@staff_required
@require_POST
def team_mission_toggle(request, team_id, mission_id):
    team = get_object_or_404(Team, id=team_id)
    mission = get_object_or_404(Mission, id=mission_id)

    tm = toggle_team_assignment(team, mission)
    if tm is None:
        messages.warning(request, 'این ماموریت سراسری است و نیازی به فعال‌سازی ندارد.')
        return redirect('dashboard:team_detail', team_id=team.id)

    messages.success(
        request,
        f'ماموریت «{mission.title}» برای تیم «{team.name}» '
        f'{"فعال" if tm.is_active else "غیرفعال"} شد.'
    )
    return redirect('dashboard:team_detail', team_id=team.id)
