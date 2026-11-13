from apps.competitions.models import CompetitionAnswer, CompetitionRegistration


def get_competition_detail_context(competition, user):
    registration = CompetitionRegistration.objects.filter(
        user=user,
        competition=competition
    ).first()

    competition_questions = (
        competition.competition_questions
        .select_related('question')
        .order_by('order')
    )
    total_questions = competition_questions.count()
    available_questions = min(total_questions, competition.max_questions)

    leaderboard = competition.get_leaderboard(limit=10)

    context = {
        'competition': competition,
        'registration': registration,
        'total_questions': total_questions,
        'available_questions': available_questions,
        'leaderboard': leaderboard,
        'is_open': competition.is_open(),
        'can_register': competition.can_register(),
        'can_play': competition.can_play(),
        'is_finished': competition.is_finished(),
    }
    return context


def get_remaining_questions(competition, registration):
    all_cqs = list(
        competition.competition_questions
        .select_related('question')
        .order_by('order')
    )

    answered_qids = set(
        CompetitionAnswer.objects.filter(
            registration=registration
        ).values_list('question_id', flat=True)
    )

    remaining_cqs = [cq for cq in all_cqs if cq.question_id not in answered_qids]

    remaining_slots = max(0, competition.max_questions - registration.total_answered)
    return remaining_cqs[:remaining_slots]
