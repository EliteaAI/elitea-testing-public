"""UI test — Onboarding tips card is displayed, starting at slide 1 / 48.

TMS: ELITEA-2235
AFS: test-specs/onboarding/l1_onboarding_tips_card_slide_1_of_48_ELITEA-2235.md

An authenticated user WITH a personal project navigating to /onboarding lands
directly in the tour + workspace-ready state (Onboarding.jsx:130-134 sets
thePrivateProjectIsReady whenever user.personal_project_id is truthy). This
spec asserts that screen's contract: the tips card at slide 1 / 48 with Tip 1's
copy, the ELITEA wordmark, and the "Your Elitea workspace is ready!" banner
carrying the "Jump in now!" button.

Fidelity: ZERO substitution — no route mock, no injected state. Every asserted
value is produced by the product from a plain authenticated navigation. In
particular this spec must NOT call OnboardingPage.mock_fresh_user_state()
(ELITEA-2231's Welcome-state mock): with personal_project_id forced to null the
page stays in the provisioning state and case step 8's banner can never render.

Coverage boundary (AFS § Entry path): the case's "first login" wording is the
route INTO this screen; the screen itself — tips card + workspace-ready banner —
is what is verified here. The first-login gate is ELITEA-2231/2232's subject.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_tips_card.py -v
"""

import re

import allure
import pytest
from pages.onboarding_page import OnboardingPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p1,
    pytest.mark.onboarding,
    pytest.mark.regression,
    pytest.mark.ui,
    pytest.mark.new,
]

UI_ELEMENT_TIMEOUT = 10_000

# Source of truth for the copy: EliteaUI
# src/[fsd]/features/onboarding/lib/constants/onboardingTips.constants.js
# (first entry; 48 entries total — onboardingTips.length feeds the "/ 48").
# The rendered text drops the markdown ** around "Quick Action:".
_EXPECTED_TIP1_TITLE = "Tip 1: Welcome to ELITEA"
_EXPECTED_TIP1_DESCRIPTION = (
    "ELITEA is your AI-powered workspace where you create intelligent agents, "
    "automate workflows with pipelines, and chat with powerful AI models. "
    "Everything you need is organized in the left sidebar for easy access."
)
_EXPECTED_TIP1_QUICK_ACTION = (
    "Quick Action: Click the ELITEA logo (top-left) to explore all available menus."
)
_EXPECTED_SLIDE_COUNTER = "1 / 48"
_EXPECTED_READY_TITLE = "Your Elitea workspace is ready!"
_EXPECTED_JUMP_IN_LABEL = "Jump in now!"


class TestOnboardingTipsCard:
    """Onboarding tips card — tour + workspace-ready state (ELITEA-2235)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2235_onboarding-onboarding-tips-card-is-displayed-on-first-login.md",
        "onetest-ai Test Case link",
    )
    def test_tips_card_displayed_at_slide_1_of_48(self, page):
        """Tips card renders at slide 1 / 48 with Tip 1's copy and the ready banner."""
        onboarding_page = OnboardingPage(page)
        console_errors: list = []
        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )

        with allure.step("Step 1 — Navigate to /onboarding as the authenticated user"):
            # Direct navigation, NOT root: '/' redirects to /onboarding only for a
            # user WITHOUT a personal project; for the standard test user it lands
            # on /chat (AFS § Risks 1).
            onboarding_page.navigate("/onboarding")
            expect(page).to_have_url(re.compile(r"/onboarding"))
            expect(onboarding_page.page_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Onboarding tips card is displayed automatically in the main content area"
        ):
            # No user action between navigation and this assertion — "automatically".
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — ELITEA logo is shown above the card, at the top centre"):
            # Case-text drift, no defect: Onboarding.jsx renders the wordmark ABOVE
            # the card (styles.logo), not inside it. Same element the user sees.
            expect(onboarding_page.page_logo).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 4 — First slide title is "Tip 1: Welcome to ELITEA"'):
            # Steps 4-6 share ONE node: TourContent.jsx renders the whole tip as a
            # single <Markdown> inside onboarding-tour-tip-content, and the heading /
            # description / quick-action children are produced by the markdown
            # renderer, so they carry no testids of their own. Asserted as three
            # contains-text checks on that node — a decomposition, not a dropped step.
            expect(onboarding_page.tour_tip_content).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.tour_tip_content).to_contain_text(_EXPECTED_TIP1_TITLE)

        with allure.step("Step 5 — Description text matches Tip 1's copy verbatim"):
            expect(onboarding_page.tour_tip_content).to_contain_text(_EXPECTED_TIP1_DESCRIPTION)

        with allure.step("Step 6 — Quick Action text matches Tip 1's copy"):
            expect(onboarding_page.tour_tip_content).to_contain_text(_EXPECTED_TIP1_QUICK_ACTION)

        with allure.step('Step 7 — Slide counter shows "1 / 48"'):
            expect(onboarding_page.tour_page_indicator).to_have_text(_EXPECTED_SLIDE_COUNTER)

        with allure.step(
            'Step 8 — "Your Elitea workspace is ready!" banner with "Jump in now!" '
            "button is visible below the card"
        ):
            expect(onboarding_page.workspace_ready_title).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(onboarding_page.workspace_ready_title).to_have_text(_EXPECTED_READY_TITLE)
            expect(onboarding_page.workspace_ready_jump_in_button).to_be_visible()
            expect(onboarding_page.workspace_ready_jump_in_button).to_have_text(
                _EXPECTED_JUMP_IN_LABEL
            )

        with allure.step(
            "Axis 2 — Previous-slide button is disabled; provisioning footer and "
            "Welcome card are absent; no console errors"
        ):
            # Independent proof that the card really is at the FIRST slide: the
            # counter text alone could be right while the position is wrong
            # (TourContent.jsx: disabled={currentStep === 1}).
            expect(onboarding_page.tour_prev_button).to_be_disabled()
            # Mutually exclusive with the workspace-ready banner in Onboarding.jsx —
            # if the footer were present, step 8 could not hold.
            expect(onboarding_page.progress_footer).to_have_count(0)
            # Confirms this is the tour state, not ELITEA-2231's Welcome state.
            expect(onboarding_page.welcome_card).to_have_count(0)
            assert not console_errors, (
                f"No console errors expected on /onboarding; got: {console_errors}"
            )
