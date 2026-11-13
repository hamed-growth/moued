from apps.questions.selectors.staff import get_staff_questions_list_context
from apps.questions.selectors.staff import get_staff_daily_questions_list_context
from django.shortcuts import render
from apps.backoffice.decorators import staff_required


@staff_required
def questions_list(request):
    q = request.GET.get('q', '').strip()
    context = get_staff_questions_list_context(q)
    return render(request, 'dashboard/questions.html', context)


@staff_required
def daily_questions_list(request):
    context = get_staff_daily_questions_list_context()
    return render(request, 'dashboard/daily_questions.html', context)
