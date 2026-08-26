"""UI test for Help Center — Sidebar Interactive Tour (ELITEA-2227).

Verifies the Sidebar Interactive Tour completes successfully by clicking
"Next" through all 17 steps: step counter + title + description advance
per step, the spotlight highlight changes target, "Back" reverts to the
previous step, "Finish" on the last step opens the "Tour Complete!" modal,
and "Done!" closes it and returns the underlying page to an interactive
state.

AFS: test-specs/help-center/l2_sidebar-interactive-tour-completes_ELITEA-2227.md

Known localhost-only quirk (not a product defect, see the AFS § Automation
Hints): the "Sidebar Interactive Tour" link is backend-CMS-served and
hardcodes ``/app`` in its href, which 404s to "Page not found" locally
(``APP_PREFIX`` is empty on localhost). The tour dialog/overlay mounts
independently of the route, so none of this test's assertions target main
content identity after the tour tab opens.

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
    """ELITEA-2227: Sidebar Interactive Tour completes via Next through all steps."""

    def test_sidebar_interactive_tour_completes_via_next(self, page):
        with allure.step('Step 1 — Navigate to Help Center and click "Sidebar Interactive Tour"'):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            expect(help_center.page_header).to_be_visible()
            expect(help_center.page_header).to_have_text("Help Center")

            tour_page = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")

        with allure.step("Step 2 — Verify the tour dialog opens on the new page at step 1/17"):
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


class TestHelpCenterSidebarTourExtras:
    """Additional Sidebar Interactive Tour behaviors — ELITEA-2226/2228/2229/2230.

    Each test targets a distinct observable not already asserted by
    ``TestHelpCenterSidebarTour.test_sidebar_interactive_tour_completes_via_next``
    (ELITEA-2227), reusing the same ``HelpCenterPage`` / ``InteractiveTourCard`` /
    ``TourCompleteCard`` infrastructure. See each case's own AFS under
    ``test-specs/help-center/`` for the full Coverage Map.
    """

    def test_sidebar_interactive_tour_starts_on_link_click(self, page):
        """ELITEA-2226: clicking the link launches the tour at step 1/17
        with the ELITEA Logo anchor, exact description text, and all three
        footer buttons (Skip/Back-disabled/Next) visible together.

        AFS: test-specs/help-center/l2_sidebar-interactive-tour-starts_ELITEA-2226.md
        """
        with allure.step("Step 1 — Navigate to Help Center"):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            expect(help_center.page_header).to_be_visible()
            expect(help_center.page_header).to_have_text("Help Center")

        with allure.step(
            'Step 2 — Locate the INTERACTIVE TOURS card and verify both tour links are displayed'
        ):
            sidebar_link = help_center.resource_link("sidebar-interactive-tour")
            chat_link = help_center.resource_link("chat-interactive-tour")
            expect(sidebar_link).to_be_visible()
            expect(chat_link).to_be_visible()

        with allure.step('Step 3 — Click "Sidebar Interactive Tour"; the tour overlay launches immediately'):
            tour_page = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")
            tour = InteractiveTourCard(tour_page)
            tour.wait_for_step()

        with allure.step(
            'Step 4 — Verify the first step is anchored to the ELITEA Logo with the exact description text'
        ):
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[0])
            # Substring match, not full-string equality — per this AFS's own
            # Concrete Handles guidance (the DOM concatenates <p> boundaries
            # with no separator, so a brittle full-string equal would break on
            # incidental whitespace/markdown-render changes even though the
            # content is correct).
            expect(tour.description).to_contain_text(
                "The ELITEA Logo in the sidebar shows the server status."
            )
            expect(tour.description).to_contain_text(
                "Green mark points that server is working."
            )
            expect(tour.description).to_contain_text(
                "Red mark points that server is updating."
            )

        with allure.step('Step 5 — Verify the step counter shows "1 / 17"'):
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")

        with allure.step("Step 6 — Verify Skip, Back (disabled), and Next are all visible together"):
            expect(tour.skip_button).to_be_visible()
            expect(tour.back_button).to_be_visible()
            expect(tour.next_button).to_be_visible()
            assert tour.is_back_disabled(), "Back should be disabled on step 1"

    def test_sidebar_interactive_tour_restarts_after_completion(self, page):
        """ELITEA-2228: a fully completed tour can be restarted from Help
        Center — clicking the link again after Finish + Done opens a fresh
        instance at step 1/17.

        AFS: test-specs/help-center/l2_sidebar-interactive-tour-restarts_ELITEA-2228.md
        """
        with allure.step(
            'Step 1 — Complete the Sidebar Interactive Tour fully via Next through all steps, Finish, Done'
        ):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            first_run = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")

            tour = InteractiveTourCard(first_run)
            tour.wait_for_step()
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")

            for step_number in range(2, TOUR_TOTAL_STEPS + 1):
                tour.click_next()
                expect(tour.step_counter).to_have_text(f"{step_number} / {TOUR_TOTAL_STEPS}")

            tour.click_finish()
            complete = TourCompleteCard(first_run)
            complete.wait_for()
            expect(complete.complete_title).to_have_text("Tour Complete!")

            complete.click_done()
            Dialog.wait_for_hidden(first_run, timeout=10000)

        with allure.step(
            'Step 2 — Navigate back to Help Center; the "Sidebar Interactive Tour" link is still visible/clickable'
        ):
            expect(help_center.resource_link("sidebar-interactive-tour")).to_be_visible()

        with allure.step('Step 3 — Click "Sidebar Interactive Tour" again; verify it restarts from step 1/17'):
            second_run = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")
            restarted_tour = InteractiveTourCard(second_run)
            restarted_tour.wait_for_step()

            expect(restarted_tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")
            expect(restarted_tour.title).to_have_text(TOUR_STEP_TITLES[0])
            assert restarted_tour.is_back_disabled(), "Back should be disabled again on a fresh restart"

    @pytest.mark.p1
    def test_sidebar_interactive_tour_skip_terminates(self, page):
        """ELITEA-2229: clicking "Skip" mid-tour removes the overlay
        immediately (no completion modal) and leaves the app fully
        interactive.

        AFS: test-specs/help-center/l1_sidebar-interactive-tour-skip-terminates_ELITEA-2229.md
        """
        with allure.step('Step 1 — Navigate to Help Center and click "Sidebar Interactive Tour"'):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            tour_page = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")

            tour = InteractiveTourCard(tour_page)
            tour.wait_for_step()

        with allure.step(
            'Step 2 — Verify the tour starts at step 1/17 with Skip, Back (disabled), and Next visible'
        ):
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")
            expect(tour.skip_button).to_be_visible()
            expect(tour.back_button).to_be_visible()
            expect(tour.next_button).to_be_visible()
            assert tour.is_back_disabled(), "Back should be disabled on step 1"

        with allure.step('Step 3 — Click "Next" twice to advance to step 3/17'):
            tour.click_next()
            expect(tour.step_counter).to_have_text(f"2 / {TOUR_TOTAL_STEPS}")
            tour.click_next()
            expect(tour.step_counter).to_have_text(f"3 / {TOUR_TOTAL_STEPS}")

        with allure.step('Step 4 — Click "Skip"'):
            tour.click_skip()

        with allure.step("Step 5/6 — Verify the tour overlay and spotlight are removed immediately"):
            # Zero matching [role="dialog"] elements is treated as "hidden" —
            # raises on timeout, doubling as the removal assertion.
            Dialog.wait_for_hidden(tour_page, timeout=10000)
            expect(tour.spotlight).to_have_count(0)

        with allure.step(
            "Step 7 — Verify the application is fully functional after skipping: sidebar navigation works"
        ):
            # Same environment-agnostic proof the covering spec uses for its
            # own "Done!" case: a real click through Playwright's
            # actionability engine fails if any overlay still intercepts
            # pointer events, so a successful click proves the tour backdrop
            # is gone and the underlying page is interactive again.
            chat = ChatPage(tour_page)
            chat.sidebar_toggle.click(timeout=5000)

    def test_sidebar_interactive_tour_back_returns_to_step_one(self, page):
        """ELITEA-2230: clicking "Back" from step 2/17 returns to step 1/17
        with matching content, and "Back" becomes disabled again.

        AFS: test-specs/help-center/l2_sidebar-interactive-tour-back-to-step-one_ELITEA-2230.md
        """
        with allure.step('Step 1 — Navigate to Help Center and click "Sidebar Interactive Tour"'):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            tour_page = help_center.open_resource_link_in_new_tab("sidebar-interactive-tour")

            tour = InteractiveTourCard(tour_page)
            tour.wait_for_step()
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[0])
            step_one_description = tour.get_description_text()

        with allure.step('Step 2 — Click "Next" to advance to step 2/17'):
            tour.click_next()
            expect(tour.step_counter).to_have_text(f"2 / {TOUR_TOTAL_STEPS}")
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[1])
            assert not tour.is_back_disabled(), "Back should be enabled once past step 1"

        with allure.step('Step 3 — Verify the tour is on step 2/17'):
            expect(tour.step_counter).to_have_text(f"2 / {TOUR_TOTAL_STEPS}")

        with allure.step('Step 4 — Click the "Back" button'):
            tour.click_back()

        with allure.step("Step 5 — Verify the tour returns to step 1/17"):
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")

        with allure.step("Step 6 — Verify the tooltip content matches step 1's content"):
            expect(tour.title).to_have_text(TOUR_STEP_TITLES[0])
            assert tour.get_description_text() == step_one_description, (
                "Description after Back-to-step-1 should match the original step 1 content"
            )

        with allure.step('Step 7 — Verify the step counter updates to "1 / 17"'):
            expect(tour.step_counter).to_have_text(f"1 / {TOUR_TOTAL_STEPS}")

        with allure.step('Step 8 — Verify the "Back" button is disabled/inactive on step 1/17'):
            assert tour.is_back_disabled(), "Back should be disabled again after returning to step 1"
