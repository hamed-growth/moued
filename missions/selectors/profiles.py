"""Compatibility exports for existing callers."""

from apps.accounts.selectors.profiles import (
    get_profile_rank,
    get_profile_history,
)

__all__ = ['get_profile_rank', 'get_profile_history']
