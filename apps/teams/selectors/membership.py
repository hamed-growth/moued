"""Read the existing single-team membership relation."""
from missions.models import TeamMember

def get_user_team(user):
    """تیم کاربر (یا None)"""
    try:
        return user.team_membership.team
    except (TeamMember.DoesNotExist, AttributeError):
        return None

