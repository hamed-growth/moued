"""Storefront inventory and purchases scoped to the authorized user."""
from django.db.models import Sum
from apps.treasure.models import TreasureCategory, TreasureItem, TreasurePurchase

def get_storefront_context(user, category_slug=""):
    """صفحه فروشگاه صندوق گنج"""

    items = TreasureItem.objects.filter(is_active=True).select_related('category')
    categories = TreasureCategory.objects.filter(is_active=True)

    active_category = None
    if category_slug:
        try:
            active_category = categories.get(slug=category_slug)
            items = items.filter(category=active_category)
        except TreasureCategory.DoesNotExist:
            pass

    items = items.order_by('-is_featured', '-created_at')

    purchases = TreasurePurchase.objects.filter(
        user=user
    ).select_related('item').order_by('-purchased_at')[:20]

    total_spent = TreasurePurchase.objects.filter(
        user=user, status__in=['pending', 'delivered']
    ).aggregate(s=Sum('item_price'))['s'] or 0
    total_bought = TreasurePurchase.objects.filter(user=user).count()

    context = {
        'items': items,
        'categories': categories,
        'active_category': active_category,
        'category_slug': category_slug,
        'purchases': purchases,
        'total_spent': total_spent,
        'total_bought': total_bought,
    }
    return context
