"""Balance writes shared by the reward and checkout workflows."""

from datetime import timedelta

from django.db.models import Case, F, Value, When
from django.utils import timezone

from apps.accounts.models import User


def add_rewards(user, points=0, coins=0):
    """Update and save the caller's user instance for the existing account API."""
    if points:
        user.total_points += points
    if coins:
        user.total_coins += coins

    today = timezone.now().date()
    if user.last_activity_date != today:
        if user.last_activity_date == today - timedelta(days=1):
            user.activity_streak += 1
        else:
            user.activity_streak = 1
        user.last_activity_date = today

    user.save()


def credit_balance(user_id, *, points, coins=None):
    """Credit using SQL increments inside the caller's reward transaction."""
    today = timezone.now().date()
    changes = {
        'total_points': F('total_points') + points,
        'last_activity_date': today,
        'activity_streak': Case(
            When(last_activity_date=today, then=F('activity_streak')),
            When(last_activity_date=today - timedelta(days=1), then=F('activity_streak') + 1),
            default=Value(1),
        ),
    }
    if coins is not None:
        changes['total_coins'] = F('total_coins') + coins
    User.objects.filter(pk=user_id).update(**changes)


def try_debit_points(user, points):
    """Attempt a conditional debit and refresh the caller's points balance."""
    debited = User.objects.filter(pk=user.pk, total_points__gte=points).update(
        total_points=F('total_points') - points,
    )
    user.refresh_from_db(fields=['total_points'])
    return bool(debited)


def try_debit_coins(user, coins):
    """Debit coins conditionally and refresh the caller's coin balance."""
    debited = User.objects.filter(pk=user.pk, total_coins__gte=coins).update(
        total_coins=F('total_coins') - coins,
    )
    user.refresh_from_db(fields=['total_coins'])
    return bool(debited)


def refund_coins(user_id, coins):
    User.objects.filter(pk=user_id).update(total_coins=F('total_coins') + coins)


def refund_points(user_id, points):
    User.objects.filter(pk=user_id).update(total_points=F('total_points') + points)
