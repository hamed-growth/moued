"""Mission completion and its reward in the same transaction."""

from django.db import transaction

from apps.wallet.services.balances import credit_balance
from apps.wallet.services.ledger import record_transaction


def save_mission_completion(completion, persist, *args, **kwargs):
    """Persist a completion, using the model's base save for the record itself."""
    if completion.pk is not None:
        return persist(*args, **kwargs)

    with transaction.atomic():
        completion.points_awarded, completion.coins_awarded = (
            completion.mission.get_rewards_for_team(completion.team)
        )
        persist(*args, **kwargs)
        award_mission_completion(completion)


def award_mission_completion(completion):
    credit_balance(
        completion.user_id, points=completion.points_awarded, coins=completion.coins_awarded,
    )
    record_transaction(
        user_id=completion.user_id,
        transaction_type='mission',
        title=f"ماموریت: {completion.mission.title}",
        points=completion.points_awarded,
        coins=completion.coins_awarded,
    )
