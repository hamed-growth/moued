"""Report queries for authorized dashboard staff."""
from django.db.models import Count

from apps.treasure.models import TreasureItem, TreasurePurchase


def get_staff_treasure_list_context():
    items = (
        TreasureItem.objects
        .select_related('category')
        .annotate(purchases_count=Count('purchases', distinct=True))
        .order_by('-created_at')
    )

    purchases = (
        TreasurePurchase.objects
        .select_related('user', 'item')
        .order_by('-purchased_at')[:100]
    )

    context = {
        'items': items,
        'purchases': purchases,
        'pending_count': TreasurePurchase.objects.filter(status='pending').count(),
    }
    return context
