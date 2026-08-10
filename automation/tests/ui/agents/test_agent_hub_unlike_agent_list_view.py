"""UI Test for ELITEA-2355 — Agent Hub: unlike an agent from the list view.

Verifies that unliking an agent from the Catalog list view (clicking the
heart icon on an agent card) toggles the heart icon's active state,
decrements the like count by 1, and persists the change after a full page
refresh.

Spec: test-specs/agent-hub/l3_agent-hub-unlike-agent-from-list-view_ELITEA-2355.md

Reuses `AgentHubPage` for navigation and like methods from ELITEA-2354;
this case exercises the inverse operation (unlike instead of like) and
verifies count persistence across a full page reload.

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error. Functionally harmless —
the like/unlike flow itself (count, icon, persistence, backend call) is
entirely correct. Same handling as ELITEA-2354 (soft assertions via
`pytest.fail()` mechanism — test stays RED until the fix ships, without
masking a genuinely new console error).

Test data: discovers a currently-liked agent dynamically (any agent with
data-liked="true" on its like button) — like counts are mutable shared
product data not suitable for hardcoding. After unliking, the count stays
decremented (this IS the test's final state — no re-like cleanup needed).

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_unlike_agent_list_view.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p3]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

_KNOWN_DEFECT_1215_PREFIX = (
    "A non-serializable value was detected in an action, in the path: `payload.updateFn`"
)


def _is_known_defect_1215(text: str) -> bool:
    """True for the known, filed, non-blocking Redux console error
    (EliteaAI/elitea-testing-public#1215) that fires on every like/unlike
    click. Matches on the warning's own stable text prefix.
    """
    return _KNOWN_DEFECT_1215_PREFIX in text


class TestAgentHubUnlikeAgentListView:
    """ELITEA-2355: Agent Hub — unlike an agent from the list view (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2355_agent-hub-unlike-an-agent-from-the-list-view.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p3
    def test_agent_hub_unlike_agent_list_view(self, page: Page):
        """Unlike an agent from the list view: decrement count, toggle state,
        and verify persistence across a full page refresh.
        """
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            agent_hub.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step("Step 2 — Navigate to 'My Liked' filter to locate liked agents"):
            # Per the AFS and surface digest: the default Trending view only shows top-6 agents.
            # To ensure we find a liked agent, navigate to "My Liked" filter which shows only
            # agents the user has liked.
            try:
                agent_hub.click_category_filter_chip("My Liked", timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_load_state("networkidle", timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_timeout(1500)  # Additional settle time for filter apply
                logger.info("Navigated to 'My Liked' filter")
            except Exception as e:
                logger.warning("Failed to navigate to My Liked filter: %s. Proceeding with Trending view.", e)
                # If My Liked filter fails, proceed with Trending view and find any liked agent there

        with allure.step("Step 2a — Locate an agent card that is already liked (data-liked='true')"):
            # Dynamically find an agent with data-liked="true" on its like button
            # (the AFS explicitly forbids hardcoding a specific agent because like counts
            # are mutable shared product data).
            liked_agent_id = None
            initial_like_count = None
            like_buttons = page.locator('[data-testid^="catalog-agent-like-button-"]')
            for i in range(like_buttons.count()):
                button = like_buttons.nth(i)
                data_liked = button.get_attribute("data-liked")
                if data_liked == "true":
                    # Extract the application ID from the testid
                    testid = button.get_attribute("data-testid")
                    # Format: catalog-agent-like-button-{id}
                    liked_agent_id = int(testid.replace("catalog-agent-like-button-", ""))
                    initial_like_count = int((button.text_content() or "0").strip())
                    logger.info(
                        "Found liked agent in 'My Liked' filter: id=%s, initial_count=%s",
                        liked_agent_id,
                        initial_like_count,
                    )
                    break

            assert liked_agent_id is not None, (
                "No liked agents found in 'My Liked' filter. Cannot proceed with unlike test."
            )
            assert initial_like_count is not None and initial_like_count >= 1, (
                f"Expected agent {liked_agent_id} to have ≥1 likes, got {initial_like_count}"
            )

        with allure.step("Step 3 — Click the heart icon (like button) on the agent card to unlike it"):
            console_errors = agent_hub.capture_console_errors()
            like_button = page.locator(f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]')
            assert like_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                f"Like button for agent {liked_agent_id} should be visible"
            )
            response = agent_hub.click_like_button(liked_agent_id, timeout=UI_ELEMENT_TIMEOUT)
            # Response should be 204 No Content for DELETE /social/like/...
            assert response.status in (201, 204), (
                f"Expected DELETE .../social/like/... to return 201 or 204, got {response.status}"
            )
            logger.info("Like button click response: %s", response.status)

        with allure.step("Step 4 — Verify the heart icon changes to an unfilled/inactive state"):
            # Wait for UI to update after the network response
            page.wait_for_timeout(500)
            data_liked_after = like_button.get_attribute("data-liked")
            assert data_liked_after == "false", (
                f"Expected data-liked='false' after unlike, got '{data_liked_after}'"
            )
            logger.info("Heart icon state changed to unfilled/inactive (data-liked='false')")

        with allure.step("Step 5 — Verify the like count decrements by 1"):
            like_count_text = (like_button.text_content() or "0").strip()
            new_like_count = int(like_count_text)
            count_delta = initial_like_count - new_like_count
            assert count_delta == 1, (
                f"Expected like count to decrement by 1, got {initial_like_count} → {new_like_count}"
            )
            logger.info("Like count decremented: %s → %s", initial_like_count, new_like_count)

        with allure.step(
            "Side-channel check — known defect #1215 console error on the unlike click "
            "(checked here, after step 5's own waits, so the async dispatch has landed)"
        ):
            unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
            assert not unexpected_errors, f"Unexpected console errors on unlike click: {unexpected_errors}"
            # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
            # soft_failures so it stays RED until the product fix ships.
            known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
            if known_defect_errors:
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                    f"non-serializable Redux console error(s) on unlike click: {len(known_defect_errors)} "
                    "occurrence(s)"
                )
            console_errors.stop()

        with allure.step("Step 6 — Refresh the page and verify the updated like count persists"):
            # Full page reload via navigation
            page.goto(page.url)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)  # Additional settle time for app initialization

            # Re-locate the like button for this agent and verify the state persisted
            like_button_refreshed = page.locator(
                f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]'
            )

            # The button should still exist and show the new count
            if like_button_refreshed.count() > 0:
                # Agent card still visible in the default view (Trending top-6 or search result)
                data_liked_refreshed = like_button_refreshed.get_attribute("data-liked")
                like_count_refreshed_text = (like_button_refreshed.text_content() or "0").strip()
                like_count_refreshed = int(like_count_refreshed_text)

                assert data_liked_refreshed == "false", (
                    f"After page refresh: expected data-liked='false', got '{data_liked_refreshed}'"
                )
                assert like_count_refreshed == new_like_count, (
                    f"After page refresh: expected like count {new_like_count}, got {like_count_refreshed}"
                )
                logger.info(
                    "Like state persisted after refresh: data-liked='false', count=%s",
                    like_count_refreshed,
                )
            else:
                # Agent not in default view (Trending top-6); use search to find it
                logger.info(
                    "Agent %s not in default Trending view after refresh; using search to verify state",
                    liked_agent_id,
                )
                # Perform a search or navigate to My Liked to find the agent
                # For now, we verify via My Liked filter since unliked agent shouldn't appear there
                agent_hub.click_category_filter_chip("My Liked", timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_timeout(1000)

                # If the agent appears in My Liked, it's still liked (test should fail)
                my_liked_buttons = page.locator(
                    f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]'
                )
                if my_liked_buttons.count() > 0:
                    # Agent still appears in My Liked → still liked → test failed
                    pytest.fail(
                        f"Agent {liked_agent_id} should NOT appear in 'My Liked' after unlike. "
                        "Like state was not persisted correctly."
                    )
                else:
                    # Agent not in My Liked → correctly unliked → persist confirmed
                    logger.info("Agent %s not in 'My Liked' after refresh → unlike persisted", liked_agent_id)

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
