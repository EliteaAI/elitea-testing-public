"""Unit tests pinning the persona-restore teardown of ELITEA-2387.

Regression coverage for the review finding on PR #1961: the teardown of
``tests/ui/settings/test_personalization_autosave_no_save_button.py`` lived in a
bare ``finally`` block that called ``personalization.get_persona()``
unconditionally. Two failures rode on that one line:

1. **It cannot run where the test most often dies.** ``get_persona()`` resolves
   ``ai-personality-persona-select-combobox`` and calls ``inner_text()``, which
   auto-waits. If the body failed at Step 4/5 the browser is on
   ``/settings/notifications``, where that element does not exist -- so the
   restore raises instead of restoring, and the shared ``${TEST_USER}`` account
   is left on the changed persona for every other spec that reads it.
2. **It masks the real failure.** An exception raised inside ``finally``
   replaces the in-flight one (the original survives only as ``__context__``),
   so a one-line assertion failure is reported as a 30s ``TimeoutError`` on an
   unrelated locator.

The fix is a route-guarded :func:`_restore_persona` plus a
:func:`_restore_persona_best_effort` wrapper used only on the already-failed
path. These tests drive both against a fake page object that reproduces the
"element absent off-route" behaviour, so they fail against the pre-fix shape.
"""

from types import SimpleNamespace

import pytest
from pages.settings_personalization_page import AI_PERSONALITY_PATH
from playwright.sync_api import Error as PlaywrightError

from tests.ui.settings.test_personalization_autosave_no_save_button import (
    _restore_persona,
    _restore_persona_best_effort,
)

BASE = "http://localhost:5173"
NOTIFICATIONS_URL = f"{BASE}/settings/notifications"
AI_PERSONALITY_URL = f"{BASE}{AI_PERSONALITY_PATH}"


class _FakePersonalizationPage:
    """Stand-in for ``SettingsPersonalizationPage`` with route-dependent reads.

    ``wait_for_persona_select`` / ``get_persona`` raise off ``ai-personality``,
    exactly as the real locator does when the element is absent -- that is the
    behaviour the pre-fix teardown walked into.
    """

    def __init__(self, url: str, persona: str, *, navigation_error: Exception | None = None):
        self.page = SimpleNamespace(url=url)
        self._persona = persona
        self._navigation_error = navigation_error
        self.calls: list[str] = []

    def open_settings_tab(self, tab_id: str, timeout: int = 30000) -> None:
        self.calls.append(f"open_settings_tab:{tab_id}")
        if self._navigation_error is not None:
            raise self._navigation_error
        self.page.url = f"{BASE}/settings/{tab_id}"

    def go_to_settings_tab(self, tab_id: str, timeout: int = 30000) -> None:  # pragma: no cover
        self.calls.append(f"go_to_settings_tab:{tab_id}")
        self.page.url = f"{BASE}/settings/{tab_id}"

    def wait_for_persona_select(self, timeout: int = 30000) -> None:
        self.calls.append("wait_for_persona_select")
        self._require_route()

    def get_persona(self) -> str:
        self.calls.append("get_persona")
        self._require_route()
        return self._persona

    def _require_route(self) -> None:
        if AI_PERSONALITY_PATH not in self.page.url:
            raise PlaywrightError(
                'Timeout 30000ms exceeded waiting for get_by_test_id'
                '("ai-personality-persona-select-combobox")'
            )


def test_restore_navigates_back_before_reading_the_persona():
    """Off-route teardown must reach AI Personality before touching the select."""
    fake = _FakePersonalizationPage(NOTIFICATIONS_URL, "Generic")

    _restore_persona(fake, "Generic")

    assert fake.calls[0] == "open_settings_tab:ai-personality", (
        "the persona must not be read before the route guard restores "
        f"/settings/ai-personality -- call order was {fake.calls}"
    )
    assert "get_persona" in fake.calls


def test_restore_does_not_renavigate_when_already_on_ai_personality():
    """The guard is a `page.url` check, not an unconditional re-navigation."""
    fake = _FakePersonalizationPage(AI_PERSONALITY_URL, "Generic")

    _restore_persona(fake, "Generic")

    assert not [c for c in fake.calls if c.startswith(("open_settings_tab", "go_to_settings_tab"))]


def test_strict_restore_still_raises_when_it_genuinely_cannot_restore():
    """A restore failure on the success path must fail the test, not be swallowed."""
    fake = _FakePersonalizationPage(
        NOTIFICATIONS_URL, "Generic", navigation_error=PlaywrightError("navigation failed")
    )

    with pytest.raises(PlaywrightError):
        _restore_persona(fake, "Generic")


def test_best_effort_restore_never_masks_an_in_flight_failure():
    """On the already-failed path the restore must swallow its own exception.

    Raised instead, it would replace the real failure in the report -- the
    exact mechanism the `finally` block had.
    """
    fake = _FakePersonalizationPage(
        NOTIFICATIONS_URL, "Generic", navigation_error=PlaywrightError("navigation failed")
    )

    _restore_persona_best_effort(fake, "Generic")  # must not raise

    assert fake.calls == ["open_settings_tab:ai-personality"]
