"""Report queries for authorized dashboard staff."""
from django.db.models import Q, Sum

from missions.models import PointTransaction


def get_staff_transactions_list_context(ttype, q):
    qs = PointTransaction.objects.select_related('user').order_by('-created_at')

    if ttype:
        qs = qs.filter(transaction_type=ttype)
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(title__icontains=q))

    totals = qs.aggregate(p=Sum('points'), c=Sum('coins'))

    context = {
        'transactions': qs[:300],
        'type': ttype,
        'q': q,
        'transaction_types': PointTransaction.TRANSACTION_TYPES,
        'total_points': totals['p'] or 0,
        'total_coins': totals['c'] or 0,
    }
    return context
