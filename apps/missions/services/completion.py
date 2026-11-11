from datetime import timedelta
from django.db.models import Case, F, Value, When
from django.utils import timezone
from missions.models import PointTransaction, User


def award_mission_completion(completion):
    today = timezone.now().date()
    User.objects.filter(pk=completion.user_id).update(
        total_points=F('total_points') + completion.points_awarded,
        total_coins=F('total_coins') + completion.coins_awarded,
        last_activity_date=today,
        activity_streak=Case(
            When(last_activity_date=today, then=F('activity_streak')),
            When(last_activity_date=today - timedelta(days=1), then=F('activity_streak') + 1),
            default=Value(1),
        ),
    )
    PointTransaction.objects.create(
        user_id=completion.user_id,
        transaction_type='mission',
        title=f"ماموریت: {completion.mission.title}",
        points=completion.points_awarded,
        coins=completion.coins_awarded,
    )
