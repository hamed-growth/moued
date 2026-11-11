"""Legacy import compatibility. Implementation lives in apps.competitions.services.rewards."""

from apps.competitions.services.rewards import (
    finalize_competition,
    finish_competition_registration,
)

__all__ = ['finalize_competition', 'finish_competition_registration']
