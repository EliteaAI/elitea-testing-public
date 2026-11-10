"""UI test for Help Center — Sidebar Interactive Tour (ELITEA-3754).

Verifies the Sidebar Interactive Tour completes successfully by clicking
"Next" through all 17 steps: step counter + title + description advance
per step, the spotlight highlight changes target, "Back" reverts to the
previous step, "Finish" on the last step opens the "Tour Complete!" modal,
and "Done!" closes it and returns the underlying page to an interactive
state.

AFS: test-specs/help-center/l2_sidebar-interactive-tour-completes_ELITEA-3754.md

DEV change (#2906): the Help Center "Interactive Tours" card ships with no
CMS-configured links ("No links configured"), so the "Sidebar Interactive Tour"
link no longer exists to click. The test opens Help Center via the sidebar "?"
icon, confirms the Interactive Tours card, and starts the tour through the
``?tour=sidebar`` deep link the app itself consumes (``useTourFromUrl``) — a
declared improvisation; the tour then runs in the same tab.

Markers:
    - ui: requires browser
    - help_center: Help Center tests
    - p2: medium priority
    - regression
"""

import logging

import allure
import pytest
from components.interactive_tour import InteractiveTourCard, TourCompleteCard
from components.mui import Dialog
from pages.chat_page import ChatPage
from pages.help_center_page import HelpCenterPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.help_center, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

# Source of truth: EliteaUI src/[fsd]/features/interactive-tours/lib/constants/
# sidebarTour.constants.js (17 entries) — confirmed against the live constants
# file during analysis.
TOUR_STEP_TITLES = [
    "ELITEA Logo",
    "Notifications",
    "Project Switcher",
    "+ Create Button",
    "Chats",
    "Agents",
    "Pipelines",
    "Skills",
    "Toolkits",
    "MCPs",
    "Credentials",
    "Applications",
    "Artifacts",
    "Settings",
    "ELITEA Catalog",
    "Help Center",
    "Support Assistant",
]
TOUR_TOTAL_STEPS = len(TOUR_STEP_TITLES)


class TestHelpCenterSidebarTour:
    """ELITEA-3754: Sidebar Interactive Tour completes via Next through all steps."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "help_center/ELITEA-3754_help-center-sidebar-interactive-tour-completes-successfully.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-3754")
    def test_sidebar_interactive_tour_completes_via_next(self, page):
        with allure.step('Step 1 — Open Help Center via the sidebar "?" icon and start the Sidebar Interactive Tour'):
            help_center = HelpCenterPage(page)
            ChatPage(page).navigate("/chat")
            help_center.open_via_sidebar_icon()
            expect(help_center.page_header).to_have_text("Help Center")
            # The tour link is CMS-configured and absent on DEV ("No links configured");
            # declared improvisation: start the tour through the ?tour=sidebar deep link.
            expect(help_center.interactive_tours_card).to_be_visible()
            help_center.start_tour_via_url("sidebar")
            tour_page = page

        with allure.step("Step 2 — Verify the tour dialog opens at step 1/17"):
            tour = InteractiveTourCard(tour_page)
            console_errors = tour.capture_console_errors()
            tour.wait_for_step()
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[0])
            expect(tour.description).to_be_visible()
            assert tour.get_description_text(), "Step 1 description should not be empty"

        with allure.step("Step 3 — Verify step counter reads 1/17 and Back is disabled"):
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")
            assert tour.is_back_disabled(), "Back button should be disabled on step 1"
            previous_bbox = tour.get_spotlight_bounding_box()

        with allure.step(
            "Step 4 — Click Next, verify advance to 2/17, title changes, Back enabled, spotlight moves"
        ):
            tour.click_next()
            expect(tour.step_counter).to_have_text(f"2 / {TOUR_TOTAL_STEPS}")
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[1])
            expect(tour.description).to_be_visible()
            assert tour.get_description_text(), "Step 2 description should not be empty"
            assert not tour.is_back_disabled(), "Back should be enabled once past step 1"
            previous_bbox = tour.wait_for_spotlight_change(previous_bbox)

        with allure.step(
            "Step 5/6 — Continue clicking Next through all remaining steps; each step's title, "
            "description, and step counter are shown and the spotlight keeps changing"
        ):
            for step_number in range(3, TOUR_TOTAL_STEPS + 1):
                expected_title = TOUR_STEP_TITLES[step_number - 1]

                tour.click_next()
                expect(tour.step_counter).to_have_text(f"{step_number} / {TOUR_TOTAL_STEPS}")
                expect(tour.title).to_have_text(expected_title)
                expect(tour.description).to_be_visible()
                assert tour.get_description_text(), f"Step {step_number} description should not be empty"

                previous_bbox = tour.wait_for_spotlight_change(previous_bbox)

                if step_number == 3:
                    with allure.step(
                        'Step 7 — At step 3, click "Back", verify counter decrements and title '
                        "reverts, then resume forward with Next"
                    ):
                        tour.click_back()
                        expect(tour.step_counter).to_have_text(f"2 / {TOUR_TOTAL_STEPS}")
                        expect(tour.title).to_have_text(TOUR_STEP_TITLES[1])

                        tour.click_next()
                        expect(tour.step_counter).to_have_text(f"3 / {TOUR_TOTAL_STEPS}")
                        expect(tour.title).to_have_text(TOUR_STEP_TITLES[2])
                        # Re-baseline the spotlight bbox — we just replayed step 3.
                        previous_bbox = tour.get_spotlight_bounding_box()

        with allure.step('Step 8 — Verify the final step (17/17) describes "Support Assistant"'):
            expect(tour.step_counter).to_have_text(f"{TOUR_TOTAL_STEPS} / {TOUR_TOTAL_STEPS}")
            expect(tour.title).to_have_text("Support Assistant")
            assert tour.get_description_text(), "Final step description should not be empty"

        with allure.step(
            'Step 9 — On 17/17 the footer buttons are Skip/Back/Finish; click "Finish"'
        ):
            expect(tour.skip_button).to_have_text("Skip")
            expect(tour.back_button).to_have_text("Back")
            expect(tour.next_button).to_have_text("Finish")
            tour.click_finish()

        with allure.step('Step 10 — Verify the "Tour Complete!" modal appears with a checkmark icon'):
            complete = TourCompleteCard(tour_page)
            complete.wait_for()
            expect(complete.complete_icon).to_be_visible()
            expect(complete.complete_title).to_have_text("Tour Complete!")

        with allure.step('Step 11 — Verify "Keep exploring:" with a "Chat Interactive Tour" option'):
            expect(complete.keep_exploring_label).to_have_text("Keep exploring:")
            chat_option = complete.keep_exploring_option("chat")
            expect(chat_option).to_be_visible()
            expect(chat_option).to_have_text("Chat Interactive Tour")

        with allure.step('Step 12 — Verify a "Done!" button is displayed'):
            expect(complete.done_button).to_be_visible()
            expect(complete.done_button).to_have_text("Done!")

        with allure.step(
            'Step 13 — Click "Done!" and verify the modal + tour backdrop are removed and the '
            "underlying page is interactive again"
        ):
            complete.click_done()
            # Playwright treats zero matching [role="dialog"] elements as
            # "hidden" — this raises on timeout, so it doubles as the
            # assertion that the modal is fully removed from the DOM.
            Dialog.wait_for_hidden(tour_page, timeout=10000)

            # Environment-agnostic form of "returns to the current project default
            # page view" (see AFS § Automation Hints): a real click through
            # Playwright's actionability engine fails if any overlay still
            # intercepts pointer events, so a successful click proves the tour
            # backdrop/blocker is gone and the page is interactive again.
            chat = ChatPage(tour_page)
            chat.sidebar_toggle.click(timeout=5000)

        with allure.step("Verify no console errors occurred during the tour run"):
            assert not console_errors, f"Unexpected console errors during the tour: {list(console_errors)}"
            console_errors.stop()
