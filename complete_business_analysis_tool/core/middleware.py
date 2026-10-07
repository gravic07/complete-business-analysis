from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.shortcuts import redirect

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponseBase

API_PATH_PREFIX = "/api/"


class SiteLoginRequiredMiddleware(LoginRequiredMiddleware):
    """Require login for every view unless it opts out with `login_not_required`.

    `/api/` routes are skipped entirely: they rely on DRF's own authentication
    (session or token) and `IsAuthenticated` default, so token-authenticated
    requests work and unauthenticated ones get a 401/403 rather than an HTML
    redirect to the login page.
    """

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponseBase],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponseBase | None:
        if request.path_info.startswith(API_PATH_PREFIX):
            return None
        return super().process_view(request, view_func, view_args, view_kwargs)


def team_not_required(view_func: Callable[..., Any]) -> Callable[..., Any]:
    """Exempt a view from `NoTeamGateMiddleware`."""
    view_func.team_required = False  # type: ignore[attr-defined]
    return view_func


class NoTeamGateMiddleware:
    """Redirect authenticated Users without a Team to the no-team page.

    Exempt: views marked `team_not_required` (the no-team page and the User's
    own profile pages), views reachable anonymously (`login_not_required` —
    client portal, PDF template, media), allauth account pages and Django
    admin. `/api/` routes are skipped: DRF's `HasTeam` default permission
    guards them, after DRF has authenticated the request (session or token).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponseBase],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponseBase | None:
        user = request.user
        if not user.is_authenticated or user.team_id is not None:
            return None
        if self._is_exempt(request, view_func):
            return None
        return redirect("no_team")

    def _is_exempt(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponseBase],
    ) -> bool:
        if request.path_info.startswith(API_PATH_PREFIX):
            return True
        if not getattr(view_func, "team_required", True):
            return True
        if not getattr(view_func, "login_required", True):
            return True
        if request.resolver_match and request.resolver_match.app_name == "admin":
            return True
        return view_func.__module__.startswith("allauth.")
