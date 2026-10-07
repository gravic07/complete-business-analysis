"""DRF permissions for the api application."""

from rest_framework.permissions import BasePermission


class HasTeam(BasePermission):
    """Deny API access to Users who aren't assigned to a Team.

    The API counterpart of `NoTeamGateMiddleware`, which guards HTML pages.
    Pair it with `IsAuthenticated`: anonymous requests pass this check so that
    DRF's own authentication failure (401/403) is what they see.
    """

    message = (
        "Your account isn't assigned to a team yet. Ask an administrator to add you."
    )

    def has_permission(self, request, view) -> bool:
        user = request.user
        return not user.is_authenticated or user.team_id is not None
