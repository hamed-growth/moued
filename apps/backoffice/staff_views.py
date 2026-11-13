from apps.backoffice.selectors.overview import get_dashboard_context
from django.shortcuts import render
from apps.backoffice.decorators import staff_required


@staff_required
def home(request):
    context = get_dashboard_context()
    return render(request, 'dashboard/home.html', context)
