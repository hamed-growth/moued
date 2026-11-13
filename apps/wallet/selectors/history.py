"""Ledger reporting only; wallet writes are not centralized here."""
from collections import OrderedDict
import jdatetime
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from apps.wallet.models import PointTransaction
from common.calendar import get_persian_month_name

def get_user_months_shamsi(user, limit=24):
    rows = (
        PointTransaction.objects
        .filter(user=user)
        .annotate(m=TruncMonth('created_at'))
        .values('m')
        .annotate(total=Sum('points'))
        .order_by('-m')
    )

    result = OrderedDict()
    for row in rows[:limit]:
        g = row['m']
        if not g:
            continue
        try:
            g_date = g.date() if hasattr(g, 'date') else g
            j = jdatetime.date.fromgregorian(date=g_date)
            key = f"{j.year}-{j.month:02d}"
            if key not in result:
                result[key] = {
                    'value': key,
                    'year': j.year,
                    'month': j.month,
                    'label': f"{get_persian_month_name(j.month)} {j.year}",
                    'total': row['total'] or 0,
                }
            else:
                result[key]['total'] += row['total'] or 0
        except Exception:
            continue

    return list(result.values())

