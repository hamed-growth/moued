"""Atomic purchase operation for the treasure storefront."""

from django.db import transaction
from django.db.models import F, Q

from apps.treasure.models import TreasureItem, TreasurePurchase
from apps.wallet.services.balances import try_debit_coins
from apps.wallet.services.ledger import record_transaction


class InsufficientCoins(Exception):
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
        debited = try_debit_coins(user, item.price)
        if debited:
            # NULL - 1 remains NULL. Recheck availability and the price used for the debit.
            reserved = TreasureItem.objects.filter(
                Q(stock__isnull=True) | Q(stock__gt=0),
                pk=item.pk, is_active=True, price=item.price,
            ).update(stock=F('stock') - 1)
            if not reserved:
                raise OutOfStock

            record_transaction(
                user_id=user.pk,
                transaction_type='treasure',
                title=f"خرید از صندوق گنج: {item.name}",
                points=0,
                coins=-item.price,
            )
            purchase = TreasurePurchase.objects.create(
                user=user,
                item=item,
                item_name=item.name,
                item_price=item.price,
                currency='coins',
                status='pending',
            )

    if not debited:
        raise InsufficientCoins(item.price - user.total_coins)
    return purchase, user.total_coins
