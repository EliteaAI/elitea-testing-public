"""UI test — Onboarding tips card expands to fullscreen and collapses with the X button.

TMS: ELITEA-2236
AFS: test-specs/onboarding/lhigh_onboarding_tips_fullscreen_expand_collapse_ELITEA-2236.md

The tips card carries an expand icon in its top-right corner. Clicking it opens
a fullscreen MUI Dialog titled "Onboarding tips" that re-renders the same slide
(image, tip text, counter) at full size with an X button. Clicking X unmounts the
dialog and returns to the embedded card, at the same slide.

Entry path and fidelity are identical to ELITEA-2235: an authenticated user WITH
a personal project navigating to /onboarding lands in the tour + workspace-ready
state directly. ZERO substitution — no route mock, no injected state.

Duplicate-testid trap: OnboardingTour.jsx keeps the EMBEDDED TourContent mounted
while the Dialog renders a SECOND copy, so onboarding-tour-tip-content /
-tip-image / -page-indicator each resolve to two visible nodes while the dialog
is open. Every in-dialog assertion therefore goes through the page object's
dialog-scoped selectors; an unscoped expect() would be a strict-mode violation.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_tips_fullscreen.py -v
"""

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

_EXPECTED_DIALOG_TITLE = "Onboarding tips"
_EXPECTED_TIP1_TITLE = "Tip 1: Welcome to ELITEA"
_EXPECTED_SLIDE_COUNTER = "1 / 48"
# Sub-pixel tolerance for layout rounding when comparing bounding boxes.
_BOX_TOLERANCE_PX = 2.0


class TestOnboardingTipsFullscreen:
    """Onboarding tips card — fullscreen expand / collapse (ELITEA-2236)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2236_onboarding-card-can-be-expanded-to-fullscreen-and-collapsed.md",
        "onetest-ai Test Case link",
    )
    def test_tips_card_expand_fullscreen_and_collapse(self, page):
        """Expand the tips card to fullscreen and collapse it back with the X button."""
        onboarding_page = OnboardingPage(page)
        console_errors: list = []
        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )

        with allure.step("Step 1 — Navigate to /onboarding; the onboarding card is visible"):
            onboarding_page.navigate("/onboarding")
            expect(onboarding_page.tour_container).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Baseline for step 4's "expands" comparison, measured before the click.
            embedded_card_box = onboarding_page.tour_container.bounding_box()
            page_container_box = onboarding_page.page_container.bounding_box()
            assert embedded_card_box and page_container_box, (
                "Embedded tips card and page container must have measurable bounding "
                "boxes before the dialog is opened"
            )

        with allure.step(
            "Step 2 — The expand/fullscreen icon is present in the card's top-right corner"
        ):
            expect(onboarding_page.tour_fullscreen_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(onboarding_page.tour_fullscreen_button).to_be_enabled()

        with allure.step("Step 3 — Click the expand icon"):
            onboarding_page.open_tour_fullscreen()

        with allure.step("Step 4 — The card expands to a fullscreen modal state"):
            # MUI's transition is covered by expect()'s auto-retry — never a sleep.
            expect(onboarding_page.tour_fullscreen_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            dialog_box = onboarding_page.tour_fullscreen_dialog.bounding_box()
            assert dialog_box, "The fullscreen dialog must have a measurable bounding box"
            # "Fullscreen" asserted as geometry, not as a MUI class name
            # (MuiDialog-paperFullScreen is a raw handle and forbidden here):
            #   a) anchored at the viewport origin,
            #   b) covers at least the whole app surface (the onboarding page shell),
            #   c) strictly larger than the embedded card it replaced.
            assert dialog_box["x"] <= _BOX_TOLERANCE_PX and dialog_box["y"] <= _BOX_TOLERANCE_PX, (
                f"Fullscreen dialog should be anchored at the viewport origin; "
                f"got x={dialog_box['x']}, y={dialog_box['y']}"
            )
            assert (
                dialog_box["width"] >= page_container_box["width"] - _BOX_TOLERANCE_PX
                and dialog_box["height"] >= page_container_box["height"] - _BOX_TOLERANCE_PX
            ), (
                f"Fullscreen dialog should cover the whole onboarding page surface; "
                f"dialog={dialog_box}, page container={page_container_box}"
            )
            assert (
                dialog_box["width"] > embedded_card_box["width"]
                and dialog_box["height"] > embedded_card_box["height"]
            ), (
                f"Fullscreen dialog should be larger than the embedded card it expands "
                f"from; dialog={dialog_box}, embedded card={embedded_card_box}"
            )
            viewport = page.viewport_size
            if viewport is not None:
                # Headless runs pin the viewport (conftest: 1366x768); headed runs use
                # no_viewport=True, where viewport_size is None and (a)-(c) above carry
                # the assertion on their own.
                assert (
                    abs(dialog_box["width"] - viewport["width"]) <= _BOX_TOLERANCE_PX
                    and abs(dialog_box["height"] - viewport["height"]) <= _BOX_TOLERANCE_PX
                ), (
                    f"Fullscreen dialog should match the viewport exactly; "
                    f"dialog={dialog_box}, viewport={viewport}"
                )

        with allure.step(
            'Step 5 — Modal title "Onboarding tips" is displayed in the enlarged view'
        ):
            expect(onboarding_page.tour_fullscreen_title).to_be_visible()
            expect(onboarding_page.tour_fullscreen_title).to_have_text(_EXPECTED_DIALOG_TITLE)

        with allure.step(
            "Step 6 — Slide image, tip text and page counter are all still visible "
            "inside the enlarged view"
        ):
            # Dialog-scoped: the embedded copy is still mounted (see module docstring).
            expect(onboarding_page.dialog_tip_image()).to_be_visible()
            expect(onboarding_page.dialog_tip_content()).to_be_visible()
            expect(onboarding_page.dialog_tip_content()).to_contain_text(_EXPECTED_TIP1_TITLE)
            expect(onboarding_page.dialog_page_indicator()).to_be_visible()
            expect(onboarding_page.dialog_page_indicator()).to_have_text(_EXPECTED_SLIDE_COUNTER)
            # Axis 2 — encodes the live DOM contract the scoping above depends on:
            # exactly two copies of the tip node while the dialog is open.
            expect(onboarding_page.tour_tip_content).to_have_count(2)

        with allure.step("Step 7 — An X (close/collapse) button is displayed in the modal"):
            expect(onboarding_page.tour_fullscreen_close_button).to_be_visible()
            expect(onboarding_page.tour_fullscreen_close_button).to_be_enabled()

        with allure.step("Step 8 — Click the X button"):
            # Escape also closes the dialog (OnboardingTour.jsx handleKeyDown); the
            # case asks for the button, so the button is what is clicked.
            onboarding_page.close_tour_fullscreen()

        with allure.step(
            "Step 9 — The modal collapses and the embedded card view is restored"
        ):
            expect(onboarding_page.tour_fullscreen_dialog).to_have_count(0)
            expect(onboarding_page.tour_fullscreen_close_button).to_have_count(0)
            expect(onboarding_page.tour_container).to_be_visible()

        with allure.step(
            "Axis 2 — Dialog truly unmounted, slide position survived the round trip, "
            "no console errors"
        ):
            # A hidden-but-mounted dialog would leave the shared testids at 2 and
            # silently break every later unscoped locator.
            expect(onboarding_page.tour_tip_content).to_have_count(1)
            # currentStep is lifted into OnboardingTour; a regression that remounted
            # TourContent would reset the user's slide.
            expect(onboarding_page.tour_page_indicator).to_have_text(_EXPECTED_SLIDE_COUNTER)
            assert not console_errors, (
                f"No console errors expected across the expand/collapse cycle; "
                f"got: {console_errors}"
            )
