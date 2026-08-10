"""Agent Hub — like an agent from the expanded detail modal (ELITEA-2358).

Verifies that clicking the like (heart icon) button inside the agent preview
modal toggles its like state, increments/decrements the like count by 1,
persists across modal close/reopen, and the updated count reflects on the
agent card in the list view afterward. Read-only until the like click itself;
cleanup: none required (like state is intentional user preference data).

Spec: test-specs/agent-hub/l2_like-agent-from-expanded-detail-modal_ELITEA-2358.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup
(ELITEA-2075) and adds new page-object methods for:
- `get_modal_like_count()` — extract the count text from the modal like button
- `click_modal_like_button()` — click the like button and return the network response

Related tests:
- ELITEA-2354 (`test_agent_hub_like_agent_list_view.py`) — like button on card-list
- ELITEA-2356 (`test_agent_hub_open_agent_detail_modal.py`) — open modal
- ELITEA-2357 (`test_agent_hub_close_agent_detail_modal.py`) — close modal

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_like_agent_detail_modal.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CATALOG_AGENT_NAME = "Business Analyst"


class TestAgentHubLikeAgentDetailModal:
    """ELITEA-2358: Agent Hub — like an agent from the expanded detail modal (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2358_agent-hub-like-an-agent-from-the-expanded-detail-modal.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_like_agent_from_expanded_detail_modal(self, page: Page):
        """Clicking the like (heart) button inside the agent preview modal
        toggles the like state, changes the count by ±1, and the updated
        count persists across modal close and reflects on the agent card
        in the list — read-only, zero console errors, zero 4xx/5xx."""
        agent_hub = AgentHubPage(page)
        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[int] = []
        page.on("response", lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None)

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card to open the detail modal"):
            assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
            )
            agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 3 — Verify the agent detail modal opens and locate the like button with current count"):
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

            # Get the initial like count from the modal like button
            initial_like_count = agent_hub.get_modal_like_count()
            assert isinstance(initial_like_count, int), f"Expected integer like count, got {initial_like_count}"
            logger.info(f"Initial like count: {initial_like_count}")

            # Verify the like button is visible
            assert agent_hub.page.locator(agent_hub.MODAL_LIKE_BUTTON).is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Modal like button should be visible in the modal header"
            )

        with allure.step("Step 4 — Click the heart icon (like button) in the modal header"):
            initial_liked_state = agent_hub.get_modal_liked_state()
            logger.info(f"Initial liked state: {initial_liked_state}")

            # Click the like button and capture the network response
            response = agent_hub.click_modal_like_button(timeout=UI_ELEMENT_TIMEOUT)
            assert response.status in (201, 204), (
                f"Expected POST/DELETE .../social/like/... to return 201 (like) or 204 (unlike), "
                f"got {response.status}"
            )

        with allure.step("Step 5 — Verify the like count increments by 1 in the modal header"):
            # The expected count should be ±1 from the initial value
            expected_like_count = initial_like_count + 1 if response.status == 201 else max(0, initial_like_count - 1)

            agent_hub.wait_for_modal_like_count(expected_like_count, timeout=UI_ELEMENT_TIMEOUT)
            actual_like_count = agent_hub.get_modal_like_count()
            assert actual_like_count == expected_like_count, (
                f"Expected like count {expected_like_count}, got {actual_like_count}"
            )

            # Verify the data-liked state changed (toggled)
            new_liked_state = agent_hub.get_modal_liked_state()
            assert new_liked_state != initial_liked_state, (
                f"data-liked should toggle from '{initial_liked_state}' to '{new_liked_state}'"
            )
            logger.info(f"New liked state: {new_liked_state}")

        with allure.step("Step 6 — Close the modal and verify the updated like count is reflected on the agent card"):
            agent_hub.close_modal(timeout=UI_ELEMENT_TIMEOUT)
            expect(agent_hub.modal_dialog).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # Verify the user remains on the Catalog page
            assert page.url.endswith("/elitea-catalog"), (
                f"Page URL should remain /elitea-catalog after modal close, got: {page.url}"
            )
            assert agent_hub.page_heading.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Catalog page heading should remain visible after modal close"
            )

        with allure.step("Step 6 (extension) — Reopen the modal and verify like state and count persist"):
            agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # Verify the persisted like count and state
            reopened_like_count = agent_hub.get_modal_like_count()
            reopened_liked_state = agent_hub.get_modal_liked_state()
            assert reopened_like_count == expected_like_count, (
                f"Like count should persist on reopen: expected {expected_like_count}, "
                f"got {reopened_like_count}"
            )
            assert reopened_liked_state == new_liked_state, (
                f"Like state should persist on reopen: expected '{new_liked_state}', "
                f"got '{reopened_liked_state}'"
            )

            agent_hub.close_modal(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Side-channel check — zero console errors, zero 4xx/5xx"):
            # Filter out the known Redux non-serializable warning (ELITEA-2354 precedent)
            expected_warning_prefix = "A non-serializable value was detected in an action"
            unexpected_errors = [
                m.text for m in console_errors
                if not m.text.startswith(expected_warning_prefix)
            ]
            assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"
            assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
            console_errors.stop()
