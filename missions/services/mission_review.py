"""Legacy import compatibility. Implementation lives in apps.missions.services.review."""

from apps.missions.services.review import (
    approve_mission_request,
    reject_mission_request,
)

__all__ = ['approve_mission_request', 'reject_mission_request']
