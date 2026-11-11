from missions.models import PointTransaction


def award_daily_answer(answer):
    if answer.is_correct:
        answer.user.add_points(answer.points_awarded)
        PointTransaction.objects.create(
            user=answer.user,
            transaction_type='daily_question',
            title=f"پاسخ صحیح به سوال روزانه: {answer.daily_question.question.text[:40]}",
            points=answer.points_awarded
        )
    else:
        answer.user.add_points(0)
