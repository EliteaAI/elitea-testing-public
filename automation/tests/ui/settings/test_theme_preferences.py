"""Settings — Preferences: Theme toggle switches Light/Dark and persists
across reload (GAP-020).

GAP-020 is a coverage-gap campaign card (cov60), not an onetest TMS case —
source: ``.agents/automation-board/batches/cov60/cases/GAP-020/source.md``.
Coverage target: ``src/[fsd]/features/settings/ui/preference/PreferenceGeneral.jsx``
(the ``ThemeModeToggle`` control) and ``src/slices/settings.js``'s
``switchMode`` reducer.

Test-data strategy (per AFS): read-only-by-default — no entity is created.
The test reads and restores the pre-existing ``localStorage['mode']`` key
(default-absent, per AFS Preconditions: the app does NOT pre-seed the
literal string ``'dark'``; the key is genuinely absent until a user first
switches). Cleanup removes the key again when it started absent, rather
than writing back the literal string ``'dark'`` — that would leave storage
in a state a fresh user never has.

This file is the dedicated GAP-020 spec; ``tests/ui/smoke/test_foundation_
cov60_surfaces_smoke.py::test_preferences_theme_toggle_switches_and_persists``
is the surface's separate, lighter standing smoke check (not a substitute —
see that file's module docstring) and stays independently.

Spec: test-specs/settings/l4_theme-toggle-light-dark-persist_GAP-020.md
"""

import logging

import allure
import pytest
from pages.user_profile_settings_page import UserProfileSettingsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
NAVIGATION_TIMEOUT = 15_000     # SPA route change + full-navigation reload

# Palette signal (per AFS § Concrete Handles — counter-intuitive, read before
# changing): Dark sets an explicit override; Light removes it entirely, so
# the correct assertion is the dark <-> transparent TRANSITION, never a
# literal "light" color.
DARK_BACKGROUND_COLOR = "rgb(14, 19, 29)"
LIGHT_BACKGROUND_COLOR = "rgba(0, 0, 0, 0)"


class TestThemePreferences:
    """Settings -> Preferences -> General: Theme toggle (Light/Dark), GAP-020.

    Flow under test (mirrors the case's 7 steps 1:1):
        1. Both Dark/Light toggle buttons render under the Theme label.
        2. The button matching localStorage['mode'] (default Dark when the
           key is absent) is selected.
        3. Clicking the non-active button flips the mode, writes
           localStorage, repaints the palette, and fires no network request.
        4. The newly-active button reflects the flip.
        5. Re-clicking the now-active button is a confirmed MUI exclusive-
           ToggleButtonGroup no-op; clicking the other button flips back.
        6. The choice survives a full-navigation page reload.
        7. Cleanup restores localStorage['mode'] (and the visible toggle) to
           the value observed at the start of the run.
    """

    @pytest.mark.p3
    @pytest.mark.regression
    def test_theme_toggle_switches_and_persists(self, page):
        """GAP-020: Theme toggle switches Light/Dark and persists across reload."""
        settings = UserProfileSettingsPage(page)
        console_errors = settings.capture_console_errors()
        original_mode = None
        original_mode_captured = False

        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate; both toggle buttons render under Theme label
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to Preferences; both toggle buttons render under Theme"):
                settings.navigate_to_preferences()

                assert settings.preferences_theme_dark_toggle.is_visible(), (
                    "Dark theme toggle button should be visible"
                )
                assert settings.preferences_theme_light_toggle.is_visible(), (
                    "Light theme toggle button should be visible"
                )

                dark_text = settings.preferences_theme_dark_toggle.text_content() or ""
                light_text = settings.preferences_theme_light_toggle.text_content() or ""
                assert "Dark" in dark_text, (
                    f"Dark toggle should carry accessible text 'Dark', got {dark_text!r}"
                )
                assert "Light" in light_text, (
                    f"Light toggle should carry accessible text 'Light', got {light_text!r}"
                )

            # ------------------------------------------------------------------
            # Step 2 — Read localStorage['mode'] + the selected toggle
            # (default: Dark when the key is absent)
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Read localStorage['mode'] and the currently-selected toggle"):
                original_mode = settings.get_theme_mode_from_storage()
                original_mode_captured = True
                effective_mode = original_mode or "dark"
                other_mode = "light" if effective_mode == "dark" else "dark"

                assert settings.is_theme_selected(effective_mode), (
                    f"'{effective_mode}' toggle should be selected "
                    f"(localStorage['mode']={original_mode!r})"
                )
                assert not settings.is_theme_selected(other_mode), (
                    f"'{other_mode}' toggle should NOT be selected while '{effective_mode}' is active"
                )

            # ------------------------------------------------------------------
            # Step 3 — With the app in Dark, click Light: mode flips,
            # localStorage updates, palette repaints, no network request
            # accompanies the switch
            # ------------------------------------------------------------------
            with allure.step(
                "Step 3 — With the app in Dark, click Light: localStorage flips, "
                "palette repaints, no network request fires"
            ):
                if effective_mode != "dark":
                    # Deterministic starting point for this step's own
                    # precondition ("with the app currently in Dark") —
                    # not itself part of the assertion window below.
                    settings.click_theme_toggle("dark")
                    assert settings.get_theme_mode_from_storage() == "dark"

                requests = settings.capture_requests_matching("")
                try:
                    settings.click_theme_toggle("light")

                    assert settings.get_theme_mode_from_storage() == "light", (
                        "localStorage['mode'] should be 'light' after clicking Light"
                    )
                    assert settings.get_body_background_color() == LIGHT_BACKGROUND_COLOR, (
                        "Body background should repaint to the Light "
                        "(override-removed/transparent) palette"
                    )
                    assert len(requests) == 0, (
                        "Theme switch is pure client-side (Redux + localStorage) — "
                        f"expected no network requests, got {len(requests)}: {list(requests)}"
                    )
                finally:
                    requests.stop()

            # ------------------------------------------------------------------
            # Step 4 — Confirm active state after switching to Light
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Confirm Light is selected and Dark is not"):
                assert settings.is_theme_selected("light"), "Light toggle should be selected after the switch"
                assert not settings.is_theme_selected("dark"), "Dark toggle should NOT be selected after the switch"

            # ------------------------------------------------------------------
            # Step 5 — Click the already-active button (confirmed no-op),
            # then click the other button to flip back to Dark
            # ------------------------------------------------------------------
            with allure.step(
                "Step 5 — Re-clicking the active (Light) button is a no-op; "
                "clicking Dark flips back"
            ):
                settings.click_theme_toggle("light")  # already active — MUI exclusive group no-op
                assert settings.get_theme_mode_from_storage() == "light", (
                    "Clicking the already-active button must be a confirmed no-op "
                    "(MUI exclusive ToggleButtonGroup) — mode must not change"
                )

                settings.click_theme_toggle("dark")
                assert settings.get_theme_mode_from_storage() == "dark", (
                    "localStorage['mode'] should be 'dark' after clicking Dark"
                )
                assert settings.get_body_background_color() == DARK_BACKGROUND_COLOR, (
                    "Body background should repaint back to the Dark palette"
                )
                assert settings.is_theme_selected("dark"), "Dark toggle should be selected"
                assert not settings.is_theme_selected("light"), "Light toggle should NOT be selected"

            # ------------------------------------------------------------------
            # Step 6 — Switch to Light once more, reload (full navigation),
            # reopen: the choice persists
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Switch to Light, reload, reopen: mode persists"):
                settings.click_theme_toggle("light")
                assert settings.get_theme_mode_from_storage() == "light"

                page.reload(wait_until="domcontentloaded")
                settings.preferences_theme_dark_toggle.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)

                assert "/settings/preferences" in page.url, (
                    "A hard reload should not redirect away from /settings/preferences"
                )
                assert settings.get_theme_mode_from_storage() == "light", (
                    "localStorage['mode'] should remain 'light' after reload"
                )
                assert settings.is_theme_selected("light"), (
                    "Light toggle should be selected once the app re-hydrates"
                )
                assert settings.get_body_background_color() == LIGHT_BACKGROUND_COLOR, (
                    "Palette should repaint light once the app re-hydrates"
                )

            # ------------------------------------------------------------------
            # Console errors — none across any step (AFS Axis-2 addition)
            # ------------------------------------------------------------------
            with allure.step("Console errors — none across any step"):
                assert not console_errors, f"Unexpected console errors: {[m.text for m in console_errors]}"

        finally:
            console_errors.stop()
            if original_mode_captured:
                with allure.step("Step 7 — Cleanup: restore localStorage['mode'] to its original value"):
                    if original_mode is None:
                        # Key was absent at the start — removing it directly
                        # is safer/faster than reproducing a click sequence
                        # to nowhere (AFS Preconditions/Cleanup finding);
                        # writing back the literal 'dark' would leave storage
                        # in a state a fresh user never has.
                        settings.set_theme_mode_in_storage(None)
                        page.reload(wait_until="domcontentloaded")
                        settings.preferences_theme_dark_toggle.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)
                    else:
                        settings.click_theme_toggle(original_mode)

                    restored_mode = settings.get_theme_mode_from_storage()
                    assert restored_mode == original_mode, (
                        f"localStorage['mode'] should be restored to {original_mode!r}, "
                        f"got {restored_mode!r}"
                    )
            else:
                logger.warning(
                    "GAP-020 cleanup: original theme mode was never captured "
                    "(early failure before Step 2) — skipping restore"
                )
