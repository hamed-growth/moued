from apps.treasure.selectors.staff import get_staff_treasure_list_context
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.treasure.models import TreasurePurchase
from apps.backoffice.decorators import staff_required


@staff_required
def treasure_list(request):
    context = get_staff_treasure_list_context()
    return render(request, 'dashboard/treasure.html', context)


@staff_required
@require_POST
def treasure_purchase_deliver(request, purchase_id):
    purchase = get_object_or_404(TreasurePurchase, id=purchase_id)
    note = request.POST.get('admin_note', '').strip()
    if purchase.deliver(admin_note=note or None):
        messages.success(request, f'درخواست «{purchase.item_name}» تأیید شد.')
    else:
        messages.info(request, 'این درخواست قبلاً بررسی شده است.')
    return redirect('dashboard:treasure')


@staff_required
@require_POST
def treasure_purchase_reject(request, purchase_id):
    purchase = get_object_or_404(TreasurePurchase, id=purchase_id)
    note = request.POST.get('admin_note', '').strip()
    if purchase.reject(admin_note=note or None):
        messages.success(request, f'درخواست «{purchase.item_name}» رد شد؛ {"سکه" if purchase.currency == "coins" else "امتیاز"} و موجودی برگشت.')
    else:
        messages.info(request, 'این درخواست قبلاً بررسی شده است.')
    return redirect('dashboard:treasure')
