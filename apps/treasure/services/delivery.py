from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.treasure.models import TreasureItem, TreasurePurchase
from apps.wallet.services.balances import refund_coins, refund_points
from apps.wallet.services.ledger import record_transaction


def deliver_purchase(purchase, admin_note=None):
    with transaction.atomic():
        changed = TreasurePurchase.objects.filter(pk=purchase.pk, status='pending').update(
            status='delivered', delivered_at=timezone.now(),
            admin_note=admin_note if admin_note is not None else purchase.admin_note,
        )
    if changed:
        purchase.refresh_from_db()
    return bool(changed)


def reject_purchase(purchase, admin_note=None):
    with transaction.atomic():
        changed = TreasurePurchase.objects.filter(pk=purchase.pk, status='pending').update(
            status='cancelled', admin_note=admin_note if admin_note is not None else purchase.admin_note,
        )
        if not changed:
            return False
        is_coin_purchase = purchase.currency == 'coins'
        if is_coin_purchase:
            refund_coins(purchase.user_id, purchase.item_price)
        else:
            refund_points(purchase.user_id, purchase.item_price)
        if purchase.item_id:
            TreasureItem.objects.filter(pk=purchase.item_id, stock__isnull=False).update(
                stock=F('stock') + 1,
            )
        record_transaction(
            user_id=purchase.user_id, transaction_type='treasure',
            title=f'بازگشت خرید ردشده: {purchase.item_name}',
            points=0 if is_coin_purchase else purchase.item_price,
            coins=purchase.item_price if is_coin_purchase else 0,
        )
    purchase.refresh_from_db()
    return True
