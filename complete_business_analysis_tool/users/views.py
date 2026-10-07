from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView

from complete_business_analysis_tool.core.middleware import team_not_required
from complete_business_analysis_tool.users.models import User

if TYPE_CHECKING:
    from django.db.models import QuerySet


@method_decorator(team_not_required, name="dispatch")
class UserDetailView(LoginRequiredMixin, DetailView):
    """A User's own profile; any other User's pk is a 404."""

    model = User
    slug_field = "id"
    slug_url_kwarg = "id"

    def get_queryset(self) -> QuerySet[User]:
        assert self.request.user.is_authenticated  # type guard
        return User.objects.filter(pk=self.request.user.pk)


user_detail_view = UserDetailView.as_view()


@method_decorator(team_not_required, name="dispatch")
class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


@method_decorator(team_not_required, name="dispatch")
class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()
