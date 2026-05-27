from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from complete_business_analysis_tool.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from complete_business_analysis_tool.users.models import User


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture(autouse=True)
def _block_real_anthropic_api(monkeypatch) -> None:
    def _raise(*args, **kwargs):
        raise RuntimeError(  # noqa: TRY003
            "Real Anthropic API called in test — inject a stub llm_client "
            "or patch the AI function at the task level.",
        )

    monkeypatch.setattr(
        "complete_business_analysis_tool.reports.ai_service.anthropic.Anthropic",
        _raise,
    )


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()
