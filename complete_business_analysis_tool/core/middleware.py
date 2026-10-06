from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.middleware import LoginRequiredMiddleware

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponseBase


class SiteLoginRequiredMiddleware(LoginRequiredMiddleware):
    """Require login for every view unless it opts out with `login_not_required`.

    `/api/` routes are skipped entirely: they rely on DRF's own authentication
    (session or token) and `IsAuthenticated` default, so token-authenticated
    requests work and unauthenticated ones get a 401/403 rather than an HTML
    redirect to the login page.
    """

    api_path_prefix = "/api/"

    def process_view(
        self,
        request: HttpRequest,
        view_func: Callable[..., HttpResponseBase],
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> HttpResponseBase | None:
        if request.path_info.startswith(self.api_path_prefix):
            return None
        return super().process_view(request, view_func, view_args, view_kwargs)
