"""Account changes for callers that have checked permission."""


def toggle_staff(user):
    user.is_staff = not user.is_staff
    user.save(update_fields=['is_staff'])


def toggle_team_manager(user):
    user.is_team_manager = not user.is_team_manager
    user.save(update_fields=['is_team_manager'])


def toggle_active(user):
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
