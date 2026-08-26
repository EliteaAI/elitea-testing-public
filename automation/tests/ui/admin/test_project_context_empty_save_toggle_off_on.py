"""UI test — an empty Project Background saves without error, toggle OFF and ON.

Two self-contained phases, each clearing the editor to empty through real
keyboard input and saving with a real click on the real Save button, asserting
the product's own PUT status, its success toast, and the view it lands on.

Case-order divergence (declared improvisation, `.agents/role-overrides.md`
§ Declared-improvisation protocol — the OBSERVABLE is unchanged, only the step
ORDER):

1. The case's step 2 -> 3 cannot be walked by clicking: with the toggle OFF,
   ``ProjectContextSavedView`` renders Edit and Edit with AI as
   ``disabled={!enabled}``. The ``/settings/project-context/edit`` route itself
   is unguarded, and bare-path navigation is this project's own established
   convention, so Phase A reaches the editor by URL — and asserts the Edit
   button IS disabled first, so the reason for the detour is test-enforced
   rather than silently worked around.
2. The case's steps 6-9 have no control to act on in sequence: after an empty
   save the server's content is "", ``hasContent`` is false, and the EMPTY
   STATE renders — which has no toggle at all. So the ON phase re-establishes
   its own precondition instead of continuing from the OFF phase.

Both are routed as clarification #1793 so the case text gets fixed rather than
this shape becoming doctrine. Nothing is dropped: both toggle states are still
exercised and the save-without-error observable is asserted in both.

Precondition substitution (declared, TRANSIT ONLY): each phase seeds a
non-empty Project Context via the API (``project_context_seed``) because that
is the only state in which the toggle exists. The clearing and the saving —
the case's actual subject — are performed through the real editor with real
keyboard input, and every asserted value comes from the product.

What the seed does and does NOT author (review round 1): the same ``PUT``
carries the enable flag, and BOTH of this case's toggle steps are ACTIONS —
step 2 "Turn the Project Context toggle OFF" and step 6 "Turn the Project
Context toggle ON". Neither is satisfied by the seed:

* **Phase A** passes no ``enabled`` at all, so the fixture carries the
  product's own flag forward (``serverData?.enabled ?? true``); case step 2 is
  then performed by a real click on the real switch.
* **Phase B** passes ``enabled=False`` — an explicit, declared PRECONDITION,
  not an observable. It restores the OFF state that Phase A's own real click
  produced and that the empty save then erased along with the toggle, so case
  step 6 has a real control to act on. Step 6 itself is a real click, waited on
  the product's own ``PUT``; the phase asserts the switch is UNCHECKED before
  it and CHECKED after, so the ON state is a product-produced state change and
  a future regression back to "re-seed ``enabled=True`` and assert checked"
  fails on the pre-click assertion.

Test case: ELITEA-2276
AFS: test-specs/settings-project-params/l3_empty-project-background-save-toggle-off-on_ELITEA-2276.md
"""

import logging

import allure
import pytest
from config import settings
from pages.project_context_page import (
    PROJECT_CONTEXT_EDIT_PATH,
    PROJECT_CONTEXT_PATH,
    ProjectContextPage,
)
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

SEED_CONTENT_PHASE_A = "ELITEA-2276 phase A seed."
SEED_CONTENT_PHASE_B = "ELITEA-2276 phase B seed."

EXPECTED_EMPTY_COUNTER = "2500 characters left."
EXPECTED_SAVE_TOAST = "Project Context saved"


class TestProjectContextEmptySaveToggleOffOn:
    """ELITEA-2276 — an empty Project Background can be saved with the toggle OFF and ON."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2276_empty-project-background-can-be-saved-whith-toggle-off-and-o.md",
        "onetest-ai Test Case link",
    )
    def test_project_context_empty_save_toggle_off_on(self, page, project_context_seed):
        """Clearing the Project Background to empty and saving succeeds in both
        toggle states: PUT 200, the 'Project Context saved' toast, and the
        empty state rendering afterwards — with no console errors."""
        context_page = ProjectContextPage(page)
        console_errors = collect_console_errors(page)

        # ---------------- Phase A — empty save with the toggle OFF (case steps 1-5) ----------------

        with allure.step(
            "Setup A — seed CONTENT only (transit only). No 'enabled' is authored: the "
            "fixture carries the product's own flag forward, and case step 2 turns the "
            "toggle OFF by a real click below"
        ):
            project_context_seed(SEED_CONTENT_PHASE_A)

        with allure.step("Step A1 — Navigate to Settings -> Project Context: the toggle card renders (case step 1)"):
            context_page.navigate_to_saved_view()
            expect(context_page.toggle_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # The seed authored no flag, so this is the PRODUCT's state — and pinning it
            # makes the OFF click below a real state change rather than a coin flip.
            expect(context_page.enable_toggle).to_be_checked()

        with allure.step(
            "Step A2 — Turn the toggle OFF: the product's own PUT returns 200, the switch is "
            "unchecked, the 'turned off' banner appears, and Edit becomes DISABLED — the live "
            "fact that forces the direct-URL route below (case step 2)"
        ):
            response = context_page.click_enable_toggle_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the Project Context PUT to return 200 when turning the toggle OFF, "
                f"got {response.status} — {response.url}"
            )
            expect(context_page.enable_toggle).not_to_be_checked()
            expect(context_page.disabled_banner).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_page.edit_button).to_be_disabled()

        with allure.step(
            "Step A3 — Open the editor by direct URL (Edit is disabled while OFF): it opens on "
            "the real saved content, with Save disabled because nothing is dirty yet"
        ):
            context_page.navigate_to_editor()
            expect(page).to_have_url(f"{settings.app_base_url}{PROJECT_CONTEXT_EDIT_PATH}")
            expect(context_page.editor_content).to_have_text(SEED_CONTENT_PHASE_A)
            expect(context_page.save_button).to_be_disabled()

        with allure.step(
            "Step A4 — Clear all content from the editor: it is empty, the character counter "
            "reads the full allowance, and Save + Discard have become enabled (case step 3)"
        ):
            context_page.clear_editor_content()
            expect(context_page.editor_content).to_have_text("")
            # Retrying assertion: the counter is a separate element driven by its own
            # slightly-lagged state update off the same CodeMirror transaction, and
            # to_have_text normalizes the product's trailing whitespace.
            expect(context_page.char_counter).to_have_text(EXPECTED_EMPTY_COUNTER)
            expect(context_page.save_button).to_be_enabled()
            expect(context_page.discard_button).to_be_enabled()

        with allure.step(
            "Step A5 — Click Save: the settings save WITHOUT error — PUT 200, the "
            "'Project Context saved' toast, the URL leaves /edit, and the empty state now "
            "renders with no toggle left to act on (case steps 4-5)"
        ):
            response = context_page.click_save_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the empty-content save to return 200 with the toggle OFF, "
                f"got {response.status} — {response.url}"
            )
            toast_text = context_page.get_toast_text()
            assert toast_text == EXPECTED_SAVE_TOAST, (
                f"Expected the success toast {EXPECTED_SAVE_TOAST!r} (the failure branch toasts "
                f"'Failed to save Project Context'), got {toast_text!r}"
            )
            expect(page).to_have_url(f"{settings.app_base_url}{PROJECT_CONTEXT_PATH}")
            expect(context_page.create_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Pins #1793: the toggle is gone entirely once content is empty, which is
            # exactly why the case's steps 6-9 cannot follow in sequence. If the product
            # is fixed to keep the toggle here, this assertion turns red and the case can
            # be re-ordered back.
            expect(context_page.enable_toggle).to_have_count(0)

        # ---------------- Phase B — empty save with the toggle ON (case steps 6-9) ----------------

        with allure.step(
            "Setup B — re-seed content with the toggle explicitly OFF (declared PRECONDITION, "
            "not an observable): it restores the OFF state step A2's real click produced and "
            "the empty save erased along with the toggle, so case step 6 has a control to act on"
        ):
            project_context_seed(SEED_CONTENT_PHASE_B, enabled=False)

        with allure.step(
            "Step B1 — Reload the page: the toggle card is back and the switch is OFF with "
            "the 'turned off' banner showing — the precondition case step 6 acts from"
        ):
            context_page.navigate_to_saved_view()
            expect(context_page.enable_toggle).not_to_be_checked()
            expect(context_page.disabled_banner).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step B2 — Turn the Project Context toggle ON by a real click on the real "
            "switch (case step 6): the product's own PUT returns 200, the switch becomes "
            "checked and the 'turned off' banner disappears — the ON state is produced by "
            "the product, never by the seed"
        ):
            response = context_page.click_enable_toggle_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the Project Context PUT to return 200 when turning the toggle back ON, "
                f"got {response.status} — {response.url}"
            )
            expect(context_page.enable_toggle).to_be_checked()
            expect(context_page.disabled_banner).to_have_count(0)

        with allure.step(
            "Step B3 — Click Edit — enabled now that the toggle is ON, the contrast with "
            "step A2 being the point: the editor opens on the real saved content"
        ):
            expect(context_page.edit_button).to_be_enabled()
            context_page.click_edit()
            expect(page).to_have_url(f"{settings.app_base_url}{PROJECT_CONTEXT_EDIT_PATH}")
            expect(context_page.editor_content).to_have_text(SEED_CONTENT_PHASE_B)

        with allure.step("Step B4 — Clear all content from the editor: empty, Save enabled (case step 7)"):
            context_page.clear_editor_content()
            expect(context_page.editor_content).to_have_text("")
            expect(context_page.save_button).to_be_enabled()

        with allure.step(
            "Step B5 — Click Save: the settings save WITHOUT error — PUT 200, the "
            "'Project Context saved' toast, and the empty state renders (case steps 8-9)"
        ):
            response = context_page.click_save_and_wait_for_put()
            assert response.status == 200, (
                f"Expected the empty-content save to return 200 with the toggle ON, "
                f"got {response.status} — {response.url}"
            )
            toast_text = context_page.get_toast_text()
            assert toast_text == EXPECTED_SAVE_TOAST, (
                f"Expected the success toast {EXPECTED_SAVE_TOAST!r}, got {toast_text!r}"
            )
            expect(context_page.create_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Side-channel check — no console errors at any step"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
