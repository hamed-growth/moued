"""Daily answer grading and first-save rewards."""

from apps.wallet.services.balances import add_rewards
from apps.wallet.services.ledger import record_transaction


def save_daily_answer(answer, persist, *args, **kwargs):
    """Grade the record on save and award only for the initial submission."""
    is_new = answer.pk is None
    question = answer.daily_question.question
    answer.is_correct = answer.selected_option == question.correct_option
    answer.points_awarded = answer.daily_question.points if answer.is_correct else 0
    persist(*args, **kwargs)
    if is_new:
        award_daily_answer(answer)


def award_daily_answer(answer):
    user = answer.user
    add_rewards(user, points=answer.points_awarded if answer.is_correct else 0)
    if answer.is_correct:
        record_transaction(
            user_id=user.pk,
            transaction_type='daily_question',
            title=f"پاسخ صحیح به سوال روزانه: {answer.daily_question.question.text[:40]}",
            points=answer.points_awarded,
        )
