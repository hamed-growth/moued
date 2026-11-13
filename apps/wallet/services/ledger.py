"""Ledger writes used by domain reward and purchase workflows."""

from apps.wallet.models import PointTransaction


def record_transaction(*, user_id, transaction_type, title, points, coins=0):
    return PointTransaction.objects.create(
        user_id=user_id, transaction_type=transaction_type, title=title, points=points, coins=coins,
    )

