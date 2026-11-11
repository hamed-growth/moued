"""Compatibility exports for existing callers."""

from apps.teams.selectors.leagues import (
    get_profile_team_leaderboard,
    get_league_rankings,
    get_ranked_teams,
)

__all__ = ['get_profile_team_leaderboard', 'get_league_rankings', 'get_ranked_teams']
