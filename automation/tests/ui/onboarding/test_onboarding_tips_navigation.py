"""UI tests — Onboarding tips-card slide navigation (Next / Previous arrows).

TMS: ELITEA-2237, ELITEA-2238, ELITEA-2239
AFS: test-specs/onboarding/l2_onboarding_tips_navigate_forward_ELITEA-2237.md
     test-specs/onboarding/l2_onboarding_tips_arrow_boundaries_ELITEA-2238.md
     test-specs/onboarding/l2_onboarding_tips_fullscreen_navigation_ELITEA-2239.md

Three cases, one file: all three share ONE subject (the tips card's navigation
arrows) and one entry path. They are NOT a family AFS — each asserts a different
shape (slide content after forward steps / boundary disabled state at both ends /
dialog-scoped bidirectional navigation), so each keeps its own AFS and its own
test class.

Entry path (identical to ELITEA-2235/2236): an authenticated user WITH a personal
project navigating directly to /onboarding lands in the tour + workspace-ready
state (Onboarding.jsx:130-134). Slide state is component-local useState, so a
fresh context always starts at "1 / 48" — no seeding, no cleanup, read-only.

Fidelity: ZERO substitution. No route mock, no injected state; every asserted
value (counter text, tip copy, image src, disabled state) is produced by the
product from a plain authenticated navigation plus real clicks. In particular
these specs must NOT call OnboardingPage.mock_fresh_user_state() — with
personal_project_id forced to null the page never leaves the provisioning state.

Duplicate-testid trap (surface digest quirk 1, extended by ELITEA-2239):
OnboardingTour keeps the EMBEDDED TourContent mounted while the Dialog renders a
SECOND copy, so onboarding-tour-{tip-content,tip-image,page-indicator,
prev-button,next-button} each resolve to two visible nodes while the dialog is
open. Every locator used in that state goes through the page object's
dialog-scoped or card-scoped class constants; an unscoped expect() would be a
strict-mode violation.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_tips_navigation.py -v
"""

import re

import allure
import pytest
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

# Source of truth for the copy: EliteaUI
# src/[fsd]/features/onboarding/lib/constants/onboardingTips.constants.js
# The rendered text drops the markdown ** around "Quick Action:".
_TIP2_TITLE = "Tip 2: Navigate the Sidebar"
_TIP2_DESCRIPTION = (
    "Your main navigation lives in the left sidebar: Chat for conversations, "
    "Agents for AI assistants, Pipelines for workflows, Collections for "
    "organization, and more. Each menu gives you quick access to create and "
    "manage your AI resources."
)
_TIP2_QUICK_ACTION = "Quick Action: Hover over each sidebar icon to see what it does."
_TIP3_TITLE = "Tip 3: Switch Between Projects"
_TIP48_TITLE = "Tip 48: View Message Execution Details"

# Slide illustrations, asserted by filename fragment of the img src. The counter
# and the tip text can both advance while the image stays stuck — a regression
# class the case's own steps cannot see.
_TIP2_IMAGE = re.compile(r"sidebar-navigation")
_TIP3_IMAGE = re.compile(r"project-selector")
_TIP48_IMAGE = re.compile(r"message-details")

# onboardingTips.length — the "/ 48" denominator and the last slide's index.
_LAST_SLIDE = 48

# Computed colour of a boundary-disabled nav arrow: TourContent.jsx sets
# styles.navButton['&:disabled'].color = 'text.disabled'. Measured live
# 2026-08-24. Paired with a not_to_have_css() on the sibling ENABLED arrow so the
# assertion means "greyed out relative to the active control", not just "some
# colour" — see the ELITEA-2238 AFS § Concrete Handles Reference.
_DISABLED_ARROW_COLOR = "rgb(104, 108, 118)"


def _collect_console_errors(page) -> list:
    """Attach an error-level console listener and return its accumulator.

    /onboarding is clean with NO filter: the known MUI focus error (#1753)
    requires the interactive-tour first-visit prompt, which only appears after
    "Jump in now!" navigates away from this page. These specs never leave it.
    """
    console_errors: list = []
    page.on(
        "console",
        lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
        if msg.type == "error"
        else None,
    )
    return console_errors


class TestOnboardingTipsForwardNavigation:
    """Onboarding tips card — forward navigation with the Next arrow (ELITEA-2237)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2237_onboarding-slides-can-be-navigated-forward-using-the-next-arrow.md",
        "onetest-ai Test Case link",
    )
    def test_next_arrow_advances_slides(self, page):
        """Two Next clicks walk the card 1 / 48 -> 2 / 48 -> 3 / 48, content following."""
        onboarding_page = OnboardingPage(page)
        console_errors = _collect_console_errors(page)

        with allure.step("Step 1 — Navigate to /onboarding; the card is at slide 1 / 48"):
            # Direct navigation, NOT root: '/' redirects to /onboarding only for a
            # user WITHOUT a personal project; the standard test user lands on /chat.
            onboarding_page.navigate("/onboarding")
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.tour_page_indicator).to_have_text(f"1 / {_LAST_SLIDE}")
            # Independent proof the card really is at the FIRST slide — the counter
            # text alone could be right while currentStep is wrong
            # (TourContent.jsx: disabled={currentStep === 1}).
            expect(onboarding_page.tour_prev_button).to_be_disabled()

        with allure.step("Step 2 — The Next (>) arrow is active and clickable"):
            expect(onboarding_page.tour_next_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.tour_next_button).to_be_enabled()

        with allure.step("Step 3 — Click the Next (>) arrow"):
            onboarding_page.click_next_slide()

        with allure.step('Step 4 — The slide counter advances to "2 / 48"'):
            expect(onboarding_page.tour_page_indicator).to_have_text(f"2 / {_LAST_SLIDE}")

        with allure.step('Step 5 — The slide content updates to "Tip 2: Navigate the Sidebar"'):
            # Steps 5-6 share ONE node: TourContent.jsx renders the whole tip as a
            # single <Markdown> inside onboarding-tour-tip-content, so the title /
            # description / quick-action children are produced by the markdown
            # renderer and carry no testids of their own. Asserted as contains-text
            # checks on that node — a decomposition, not a dropped step.
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP2_TITLE)

        with allure.step("Step 6 — The description for slide 2 is displayed correctly"):
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP2_DESCRIPTION)
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP2_QUICK_ACTION)
            # Axis 2 — the illustration follows the slide, and leaving slide 1
            # re-enables the Previous arrow.
            expect(onboarding_page.tour_tip_image).to_have_attribute("src", _TIP2_IMAGE)
            expect(onboarding_page.tour_prev_button).to_be_enabled()

        with allure.step("Step 7 — Click the Next (>) arrow again"):
            onboarding_page.click_next_slide()

        with allure.step('Step 8 — The counter advances to "3 / 48" with new tip content'):
            expect(onboarding_page.tour_page_indicator).to_have_text(f"3 / {_LAST_SLIDE}")
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP3_TITLE)
            expect(onboarding_page.tour_tip_image).to_have_attribute("src", _TIP3_IMAGE)

        with allure.step("Axis 2 — No console errors across the navigation flow"):
            assert not console_errors, (
                f"No console errors expected while navigating /onboarding; "
                f"got: {console_errors}"
            )


class TestOnboardingTipsArrowBoundaries:
    """Onboarding tips card — arrows are inactive at both ends of the range (ELITEA-2238)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2238_onboarding-left-arrow-is-inactive-on-slide-1-and-right-arrow-is-"
        "inactive-on-slide-48.md",
        "onetest-ai Test Case link",
    )
    def test_arrows_inactive_at_first_and_last_slide(self, page):
        """Previous is inactive at 1 / 48, Next is inactive at 48 / 48; neither navigates."""
        onboarding_page = OnboardingPage(page)
        console_errors = _collect_console_errors(page)

        with allure.step("Step 1 — Navigate to /onboarding; the card is at slide 1 / 48"):
            onboarding_page.navigate("/onboarding")
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.tour_page_indicator).to_have_text(f"1 / {_LAST_SLIDE}")

        with allure.step(
            "Step 2 — The Previous (<) arrow is visually inactive (disabled, greyed out) "
            "on slide 1 / 48"
        ):
            expect(onboarding_page.tour_prev_button).to_be_disabled()
            # "Visually inactive" asserted as the greyed colour AND unclickability,
            # not only the disabled property.
            expect(onboarding_page.tour_prev_button).to_have_css(
                "color", _DISABLED_ARROW_COLOR
            )
            expect(onboarding_page.tour_prev_button).to_have_css("pointer-events", "none")
            # Axis 2 — the OPPOSITE arrow is active. Without this, to_be_disabled()
            # would also pass if the product disabled BOTH arrows.
            expect(onboarding_page.tour_next_button).to_be_enabled()
            expect(onboarding_page.tour_next_button).not_to_have_css(
                "color", _DISABLED_ARROW_COLOR
            )

        with allure.step(
            "Step 3 — Click the Previous (<) arrow; no navigation occurs (stays on 1 / 48)"
        ):
            # force=True is required, not a shortcut: the disabled control has
            # pointer-events: none, so a normal click fails Playwright's
            # actionability check and would read like a product failure. Forcing
            # dispatches a real mouse click at the control's position — exactly what
            # a user does — and the product's own handler ignores it. The asserted
            # observable (counter unchanged) is still produced by the product.
            onboarding_page.tour_prev_button.click(force=True)
            expect(onboarding_page.tour_page_indicator).to_have_text(f"1 / {_LAST_SLIDE}")

        with allure.step(
            "Step 4 — Click the Next (>) arrow repeatedly until slide 48 / 48 is reached"
        ):
            # Bounded by the constant, NOT by `while not disabled`: an off-by-one or
            # a skipped slide must FAIL rather than let the loop silently adapt.
            # The per-click assertion is what makes "repeatedly" a contract — a
            # wrap-around or a stuck slide fails at the click that caused it.
            for step in range(2, _LAST_SLIDE + 1):
                onboarding_page.click_next_slide()
                expect(onboarding_page.tour_page_indicator).to_have_text(
                    f"{step} / {_LAST_SLIDE}"
                )

        with allure.step('Step 5 — The slide counter shows "48 / 48"'):
            expect(onboarding_page.tour_page_indicator).to_have_text(
                f"{_LAST_SLIDE} / {_LAST_SLIDE}"
            )

        with allure.step(
            'Step 6 — The slide content shows "Tip 48: View Message Execution Details"'
        ):
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP48_TITLE)
            # Axis 2 — the illustration followed the walk to the last slide.
            expect(onboarding_page.tour_tip_image).to_have_attribute("src", _TIP48_IMAGE)

        with allure.step(
            "Step 7 — The Next (>) arrow is visually inactive (disabled, greyed out) "
            "on slide 48 / 48"
        ):
            expect(onboarding_page.tour_next_button).to_be_disabled()
            expect(onboarding_page.tour_next_button).to_have_css(
                "color", _DISABLED_ARROW_COLOR
            )
            expect(onboarding_page.tour_next_button).to_have_css("pointer-events", "none")
            # Axis 2 — mirror of step 2: the opposite arrow stays active here.
            expect(onboarding_page.tour_prev_button).to_be_enabled()
            expect(onboarding_page.tour_prev_button).not_to_have_css(
                "color", _DISABLED_ARROW_COLOR
            )

        with allure.step(
            "Step 8 — Click the Next (>) arrow; no navigation occurs (stays on 48 / 48)"
        ):
            onboarding_page.tour_next_button.click(force=True)
            expect(onboarding_page.tour_page_indicator).to_have_text(
                f"{_LAST_SLIDE} / {_LAST_SLIDE}"
            )

        with allure.step("Axis 2 — No console errors across the full 1 -> 48 walk"):
            assert not console_errors, (
                f"No console errors expected while walking the whole tour; "
                f"got: {console_errors}"
            )


class TestOnboardingTipsFullscreenNavigation:
    """Onboarding tips card — navigation from the fullscreen dialog (ELITEA-2239)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2239_onboarding-slides-can-be-navigated-forward-and-backward-from-the-"
        "enlarged-fullscreen-state.md",
        "onetest-ai Test Case link",
    )
    def test_navigate_forward_and_backward_in_fullscreen(self, page):
        """Forward twice and back once inside the dialog; the embedded card follows."""
        onboarding_page = OnboardingPage(page)
        console_errors = _collect_console_errors(page)

        with allure.step("Step 1 — Navigate to /onboarding; the card is at slide 1 / 48"):
            onboarding_page.navigate("/onboarding")
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(onboarding_page.tour_page_indicator).to_have_text(f"1 / {_LAST_SLIDE}")

        with allure.step("Step 2 — Click the expand icon to open the enlarged fullscreen view"):
            # The dialog's GEOMETRY (is it really fullscreen) is ELITEA-2236's
            # subject and is deliberately not re-asserted here.
            onboarding_page.open_tour_fullscreen()
            expect(onboarding_page.tour_fullscreen_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step('Step 3 — The slide counter shows "1 / 48" in the enlarged state'):
            expect(onboarding_page.dialog_page_indicator()).to_have_text(f"1 / {_LAST_SLIDE}")
            # Axis 2 — the boundary rule holds for the DIALOG's copy of the arrows
            # too, not only the embedded card's (which is ELITEA-2238's subject).
            expect(onboarding_page.dialog_prev_button()).to_be_disabled()
            expect(onboarding_page.dialog_next_button()).to_be_enabled()
            # Axis 2 — encodes the live DOM contract every scoped locator here
            # depends on: exactly two copies of each arrow while the dialog is open.
            expect(onboarding_page.tour_prev_button).to_have_count(2)
            expect(onboarding_page.tour_next_button).to_have_count(2)

        with allure.step("Step 4 — Click the right arrow (>) in the enlarged view"):
            onboarding_page.click_dialog_next_slide()

        with allure.step('Step 5 — The counter advances to "2 / 48" and the content updates'):
            expect(onboarding_page.dialog_page_indicator()).to_have_text(f"2 / {_LAST_SLIDE}")
            expect(onboarding_page.dialog_tip_content()).to_contain_text(_TIP2_TITLE)
            expect(onboarding_page.dialog_tip_image()).to_have_attribute("src", _TIP2_IMAGE)
            expect(onboarding_page.dialog_prev_button()).to_be_enabled()
            # Step 9's first half, checked at every navigation point: currentStep is
            # lifted into OnboardingTour, so the EMBEDDED card must report the same
            # slide. Card-scoped — the shared testid resolves to two nodes here.
            expect(onboarding_page.card_page_indicator()).to_have_text(f"2 / {_LAST_SLIDE}")

        with allure.step("Step 6 — Click the right arrow (>) again to advance to slide 3 / 48"):
            onboarding_page.click_dialog_next_slide()
            expect(onboarding_page.dialog_page_indicator()).to_have_text(f"3 / {_LAST_SLIDE}")
            expect(onboarding_page.dialog_tip_content()).to_contain_text(_TIP3_TITLE)
            expect(onboarding_page.dialog_tip_image()).to_have_attribute("src", _TIP3_IMAGE)
            expect(onboarding_page.card_page_indicator()).to_have_text(f"3 / {_LAST_SLIDE}")

        with allure.step("Step 7 — Click the left arrow (<) in the enlarged view"):
            onboarding_page.click_dialog_prev_slide()

        with allure.step(
            'Step 8 — The counter returns to "2 / 48" and the previous slide content is shown'
        ):
            expect(onboarding_page.dialog_page_indicator()).to_have_text(f"2 / {_LAST_SLIDE}")
            expect(onboarding_page.dialog_tip_content()).to_contain_text(_TIP2_TITLE)
            # The image re-check is what proves the CONTENT went back, not just the
            # counter label.
            expect(onboarding_page.dialog_tip_image()).to_have_attribute("src", _TIP2_IMAGE)

        with allure.step(
            "Step 9 — Navigation is consistent with the collapsed card view: both views "
            "report the same slide, and the slide survives collapsing the dialog"
        ):
            # The case's step 9 is a prose judgement, so it is asserted as the two
            # concrete invariants the product actually guarantees (AFS § Case-text
            # note): both copies agree while the dialog is open, and the slide
            # reached inside the dialog is still current after it closes.
            expect(onboarding_page.card_page_indicator()).to_have_text(f"2 / {_LAST_SLIDE}")
            expect(onboarding_page.card_tip_content()).to_contain_text(_TIP2_TITLE)
            onboarding_page.close_tour_fullscreen()
            expect(onboarding_page.tour_fullscreen_dialog).to_have_count(0)
            expect(onboarding_page.tour_page_indicator).to_have_text(f"2 / {_LAST_SLIDE}")
            expect(onboarding_page.tour_tip_content).to_contain_text(_TIP2_TITLE)
            # The collapsed card's arrows behave the same as before: Previous is
            # enabled off slide 1, Next is enabled below slide 48.
            expect(onboarding_page.tour_prev_button).to_be_enabled()
            expect(onboarding_page.tour_next_button).to_be_enabled()

        with allure.step("Axis 2 — No console errors across the fullscreen navigation flow"):
            assert not console_errors, (
                f"No console errors expected while navigating in fullscreen; "
                f"got: {console_errors}"
            )
