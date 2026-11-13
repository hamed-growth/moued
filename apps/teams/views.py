from apps.teams.selectors.overview import get_league_context
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def league_list(request):
    context = get_league_context(request.user, request.GET.get('month', ''))
    return render(request, 'missions/league_list.html', context)
