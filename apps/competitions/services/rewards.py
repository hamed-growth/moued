"""Atomic competition payouts. Callers own authorization and request validation."""

from django.db import transaction
from django.utils import timezone

from apps.competitions.models import Competition, CompetitionRegistration
from apps.wallet.services.balances import credit_balance
from apps.wallet.services.ledger import record_transaction


def _award_competition_points(user_id, points, title):
    credit_balance(user_id, points=points)
    record_transaction(
        user_id=user_id, transaction_type='competition', title=title, points=points,
    )


def finalize_competition(competition):
    """Finalize once and update the supplied competition status on success."""
    with transaction.atomic():
        claimed = Competition.objects.filter(pk=competition.pk).exclude(status='finished').update(status='finished')
        if not claimed:
            return False
        current = Competition.objects.get(pk=competition.pk)
        top3 = current.registrations.order_by('-total_correct', 'finished_at')[:3]
        prizes = (current.first_prize_points, current.second_prize_points, current.third_prize_points)
        for rank, (reg, prize) in enumerate(zip(top3, prizes), start=1):
            if reg.total_correct > 0:
                _award_competition_points(reg.user_id, prize, f"جایزه رتبه {rank} مسابقه «{current.title}»")
                reg.rank = rank
                reg.save(update_fields=['rank'])
    competition.status = 'finished'
    return True


def finish_competition_registration(registration):
    """Claim completion, refresh the supplied registration and pay its rewards."""
    with transaction.atomic():
        claimed = CompetitionRegistration.objects.filter(pk=registration.pk, is_completed=False).update(
            is_completed=True, finished_at=timezone.now(),
        )
        registration.refresh_from_db()
        if not claimed:
            return False
        competition = registration.competition
        if registration.score > 0:
            _award_competition_points(
                registration.user_id, registration.score, f"امتیاز پاسخ‌های صحیح مسابقه «{competition.title}»",
            )
        if competition.participation_bonus > 0:
            _award_competition_points(
                registration.user_id, competition.participation_bonus, f"جایزه شرکت در مسابقه «{competition.title}»",
            )
    return True
