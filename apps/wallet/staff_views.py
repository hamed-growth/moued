from apps.wallet.selectors.staff import get_staff_transactions_list_context
from django.shortcuts import render
from apps.backoffice.decorators import staff_required


@staff_required
def transactions_list(request):
    ttype = request.GET.get('type', '')
    q = request.GET.get('q', '').strip()
    context = get_staff_transactions_list_context(ttype, q)
    return render(request, 'dashboard/transactions.html', context)
