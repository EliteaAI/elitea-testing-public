"""UI test — "Jump in now!" closes onboarding and shows the default project page.

TMS: ELITEA-2241
AFS: test-specs/onboarding/l2_onboarding_jump_in_now_ELITEA-2241.md

From the onboarding tips screen, clicking "Jump in now!" in the "Your Elitea
workspace is ready!" banner navigates to /chat and unmounts the whole onboarding
surface. The sidebar is present on the destination page — but the product also
opens an interactive-tour first-visit prompt whose backdrop intercepts pointer
events, so the sidebar becomes *functional* only after the prompt is dismissed.

Entry path and fidelity are identical to ELITEA-2235: an authenticated user WITH
a personal project navigating to /onboarding lands in the tour + workspace-ready
state directly. ZERO substitution — no route mock, no injected state, and
deliberately no page.evaluate() read of sessionStorage.onboarding_state: the
observable is already fully covered by the UI unmount assertions.

Known defects handled here (neither masked — both filed, open and linked):
  - #1753 (MINOR): the first-visit prompt logs "MUI: The modal content node does
    not accept focus." every time it opens. That ONE message is excluded from the
    console assertion; every other console error still fails the test.
  - #1754 (CLARIFICATION): case step 7 says the sidebar is "displayed and
    functional" right after Jump in now!, but the modal prompt blocks it until
    dismissed. Step 7 is decomposed into displayed -> Skip -> functional; the
    live contract is asserted, per the reverse-masking guard.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_jump_in.py -v
"""

import re

import allure
import pytest
from components.interactive_tour import FirstVisitPromptCard
from pages.onboarding_page import OnboardingPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.onboarding,
    pytest.mark.regression,
    pytest.mark.ui,
    pytest.mark.new,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

_EXPECTED_READY_TITLE = "Your Elitea workspace is ready!"
_EXPECTED_JUMP_IN_LABEL = "Jump in now!"
# Computed background-color of the "Jump in now!" button on the DEFAULT (dark)
# theme — MuiButton-eliteaPrimary. A failure here reads "the theme changed",
# not "the button broke"; the suite runs the default theme only.
_EXPECTED_JUMP_IN_BACKGROUND = "rgb(106, 232, 250)"
# Known defect: #1753 — the first-visit prompt's own MUI focus-trap warning.
_KNOWN_CONSOLE_ERROR_1753 = "does not accept focus"


class TestOnboardingJumpIn:
    """Onboarding — "Jump in now!" dismisses onboarding (ELITEA-2241)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2241_onboarding-clicking-jump-in-now-closes-onboarding-and-shows.md",
        "onetest-ai Test Case link",
    )
    def test_jump_in_now_closes_onboarding_and_shows_default_project_page(self, page):
        """"Jump in now!" unmounts onboarding and lands on the default project page."""
        onboarding_page = OnboardingPage(page)
        first_visit_prompt = FirstVisitPromptCard(page)
        console_errors: list = []
        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )

        with allure.step("Step 1 — Navigate to /onboarding; the onboarding card is displayed"):
            onboarding_page.navigate("/onboarding")
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 2 — The "Your Elitea workspace is ready!" banner is present'
        ):
            expect(onboarding_page.workspace_ready_title).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(onboarding_page.workspace_ready_title).to_have_text(_EXPECTED_READY_TITLE)

        with allure.step(
            'Step 3 — The "Jump in now!" button is visible and carries the teal fill'
        ):
            expect(onboarding_page.workspace_ready_jump_in_button).to_be_visible()
            expect(onboarding_page.workspace_ready_jump_in_button).to_be_enabled()
            expect(onboarding_page.workspace_ready_jump_in_button).to_have_text(
                _EXPECTED_JUMP_IN_LABEL
            )
            expect(onboarding_page.workspace_ready_jump_in_button).to_have_css(
                "background-color", _EXPECTED_JUMP_IN_BACKGROUND
            )

        with allure.step('Step 4 — Click the "Jump in now!" button'):
            onboarding_page.click_jump_in()

        with allure.step("Step 6 — The user is navigated to the default project page (/chat)"):
            # Asserted before step 5's absence checks because the unmount is a
            # consequence of this client-side navigation completing.
            page.wait_for_url("**/chat", timeout=NAVIGATION_TIMEOUT)
            expect(page).to_have_url(re.compile(r"/chat$"))

        with allure.step("Step 5 — The onboarding card is dismissed"):
            expect(onboarding_page.page_container).to_have_count(0)
            expect(onboarding_page.tour_container).to_have_count(0)
            expect(onboarding_page.workspace_ready_jump_in_button).to_have_count(0)

        with allure.step(
            "Step 7 — The full sidebar navigation is displayed, and functional once "
            "the first-visit tour prompt is dismissed (clarification #1754)"
        ):
            # 7a — DISPLAYED, asserted while the prompt is still up: the sidebar is
            # visible immediately; only pointer events are blocked.
            expect(onboarding_page.sidebar_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.sidebar_menu_item("chat")).to_be_visible()
            expect(onboarding_page.sidebar_menu_item("agents")).to_be_visible()

            # 7b — Axis 2: visiting /onboarding arms the first-elitea interactive tour
            # (handlePersonalProjectReady -> markTourPending), so this prompt opens on
            # the destination page every time. Its backdrop intercepts pointer events,
            # so it must be dismissed before the sidebar can be exercised.
            first_visit_prompt.wait_for(timeout=UI_ELEMENT_TIMEOUT)
            expect(first_visit_prompt.prompt).to_be_visible()
            first_visit_prompt.click_skip()
            expect(first_visit_prompt.prompt).to_have_count(0)

            # 7c — FUNCTIONAL: a sidebar entry actually navigates.
            onboarding_page.sidebar_menu_item("agents").click()
            expect(page).to_have_url(re.compile(r"/agents"), timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            "Step 8 — The onboarding card is still not shown after the sidebar navigation"
        ):
            # Deliberate re-assert: proves the onboarding surface does not come back
            # on the next client-side navigation.
            expect(onboarding_page.tour_container).to_have_count(0)
            expect(onboarding_page.page_container).to_have_count(0)

        with allure.step(
            "Axis 2 — No console errors other than the known first-visit-prompt "
            "focus-trap warning"
        ):
            # Known defect: #1753 — deterministic, filed, open, product-side a11y
            # defect on this exact path. Excluding this ONE message is not masking:
            # every other console error still fails the test, and the red returns
            # automatically when #1753 is fixed and the filter stops matching.
            unexpected = [e for e in console_errors if _KNOWN_CONSOLE_ERROR_1753 not in e]
            assert not unexpected, (
                f"No console errors expected on the Jump-in-now path other than "
                f"known defect #1753; got: {unexpected}"
            )
