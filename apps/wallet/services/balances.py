from datetime import timedelta

from django.utils import timezone


def add_rewards(user, points=0, coins=0):
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
