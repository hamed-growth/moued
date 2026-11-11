"""Submission workflow for the competitions domain."""

from datetime import timedelta

from django.utils import timezone

from missions.models import CompetitionAnswer, CompetitionQuestion, CompetitionRegistration
from apps.competitions.selectors.detail import get_remaining_questions
from apps.submissions import SubmissionRejected


def submit_competition_answer(user, competition, question_id, raw_option):
    if not competition.can_play():
        raise SubmissionRejected('این مسابقه در حال حاضر قابل بازی نیست.')

    if not competition.is_open():
        raise SubmissionRejected('این مسابقه در حال برگزاری نیست.')

    competition_question = CompetitionQuestion.objects.get(
        competition=competition,
        question_id=question_id
    )
    question = competition_question.question

    registration = CompetitionRegistration.objects.filter(
        user=user,
        competition=competition
    ).first()

    if not registration:
        raise SubmissionRejected('ابتدا در مسابقه ثبت\u200cنام کنید.')

    if registration.is_completed:
        raise SubmissionRejected('شما این مسابقه را به پایان رسانده\u200cاید.')

    if registration.is_time_expired():
        registration.finish()
        raise SubmissionRejected('زمان مجاز شما به پایان رسیده است.', completed=True)

    registration.start()

    if registration.total_answered >= competition.max_questions:
        registration.finish()
        raise SubmissionRejected('به حداکثر تعداد سوال رسیده\u200cاید.', completed=True)

    if CompetitionAnswer.objects.filter(
        registration=registration, question=question
    ).exists():
        raise SubmissionRejected('قبلاً به این سوال پاسخ داده\u200cاید.')

    try:
        selected_option = int(raw_option)
    except (ValueError, TypeError):
        raise SubmissionRejected('گزینه نامعتبر است.')

    if selected_option not in (1, 2, 3, 4):
        raise SubmissionRejected('گزینه نامعتبر است.')

    points = competition_question.get_points()
    answer = CompetitionAnswer.objects.create(
        registration=registration,
        question=question,
        selected_option=selected_option,
        is_correct=(selected_option == question.correct_option),
        points_awarded=points if selected_option == question.correct_option else 0,
    )

    registration.add_result(answer.is_correct, answer.points_awarded)

    if registration.total_answered >= competition.max_questions:
        registration.finish()
    return answer, registration


def prepare_competition_play(user, competition):
    if not competition.can_play():
        return ('finished' if competition.is_finished() else 'unavailable'), None

    registration = CompetitionRegistration.objects.filter(
        user=user,
        competition=competition
    ).first()

    if not registration:
        return 'unregistered', None

    if registration.is_completed:
        return 'completed', None

    if registration.is_time_expired():
        registration.finish()
        return 'expired', None

    registration.start()

    questions_to_show = get_remaining_questions(competition, registration)

    if not questions_to_show:
        if not registration.is_completed:
            registration.finish()
        return 'exhausted', None

    time_remaining = 0
    if competition.time_limit_minutes > 0 and registration.started_at:
        deadline = registration.started_at + timedelta(
            minutes=competition.time_limit_minutes
        )
        remaining = (deadline - timezone.now()).total_seconds()
        time_remaining = max(0, int(remaining))

    context = {
        'competition': competition,
        'registration': registration,
        'competition_questions': questions_to_show,
        'total_remaining': len(questions_to_show),
        'time_remaining': time_remaining,
        'initial_score': registration.score,
        'initial_correct': registration.total_correct,
        'initial_answered': registration.total_answered,
    }
    return None, context


def start_participation(user, competition):
    if not competition.can_play():
        raise SubmissionRejected('این مسابقه در حال حاضر قابل بازی نیست.')
    registration, _ = CompetitionRegistration.objects.get_or_create(
        user=user, competition=competition,
    )
    if registration.is_completed:
        raise SubmissionRejected('شما قبلاً این مسابقه را تمام کرده‌اید.')
    registration.start()
    return registration


def register_participant(user, competition):
    if not competition.can_register():
        raise SubmissionRejected('امکان ثبت‌نام در این مسابقه وجود ندارد.')
    _, created = CompetitionRegistration.objects.get_or_create(
        user=user, competition=competition,
    )
    return created
