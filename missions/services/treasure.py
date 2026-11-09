"""Atomic purchase operation for the treasure storefront."""

from django.db import transaction
from django.db.models import F, Q

from ..models import PointTransaction, TreasureItem, TreasurePurchase, User


class InsufficientPoints(Exception):
    def __init__(self, shortfall):
        self.shortfall = shortfall
        super().__init__(shortfall)


class OutOfStock(Exception):
    pass


def purchase_treasure_item(user, item_id):
    """Purchase an active item for the authenticated caller. Return (purchase, balance)."""
    item = TreasureItem.objects.get(pk=item_id, is_active=True)
    if not item.is_available():
        raise OutOfStock

    with transaction.atomic():
        # Start with a write so SQLite doesn't have to upgrade a read transaction.
        debited = User.objects.filter(pk=user.pk, total_points__gte=item.price).update(
            total_points=F('total_points') - item.price,
        )
        user.refresh_from_db(fields=['total_points'])
        if debited:
            # NULL - 1 remains NULL. Recheck availability and the price used for the debit.
            reserved = TreasureItem.objects.filter(
                Q(stock__isnull=True) | Q(stock__gt=0),
                pk=item.pk, is_active=True, price=item.price,
            ).update(stock=F('stock') - 1)
            if not reserved:
                raise OutOfStock

            PointTransaction.objects.create(
                user=user,
                transaction_type='treasure',
                title=f"خرید از صندوق گنج: {item.name}",
                points=-item.price,
                coins=0,
            )
            purchase = TreasurePurchase.objects.create(
                user=user,
                item=item,
                item_name=item.name,
                item_price=item.price,
                status='pending',
            )

    if not debited:
        raise InsufficientPoints(item.price - user.total_points)
    return purchase, user.total_points
