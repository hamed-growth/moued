import logging
from apps.competitions.selectors.staff import get_staff_competitions_list_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import DatabaseError
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.competitions.models import Competition
from apps.competitions.models import Competition
from apps.backoffice.decorators import staff_required

logger = logging.getLogger(__name__)


@staff_required
def competitions_list(request):
    context = get_staff_competitions_list_context()
    return render(request, 'dashboard/competitions.html', context)


@staff_required
@require_POST
def competition_finalize(request, comp_id):
    comp = get_object_or_404(Competition, id=comp_id)
    try:
        finalized = comp.finalize()
    except DatabaseError:
        logger.exception("Competition finalization database operation failed")
        return HttpResponse('پایان مسابقه ثبت نشد. لطفاً دوباره تلاش کنید.', status=503)
    if finalized:
        messages.success(request, f'مسابقه «{comp.title}» پایان یافت و جوایز اهدا شد.')
    else:
        messages.info(request, 'این مسابقه قبلاً پایان یافته است.')
    return redirect('dashboard:competitions')
