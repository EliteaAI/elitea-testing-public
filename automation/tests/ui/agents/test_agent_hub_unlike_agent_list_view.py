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
from playwright.sync_api import Page

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
        liked_agent_id = None
        initial_like_count = None

        with allure.step("Step 1 — Navigate to Agent Hub and capture applications"):
            applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"
            logger.info("Agent Hub (Catalog) page loaded with %d applications", len(applications))

        with allure.step("Step 2 — Find an already-liked agent"):
            # Use the bulk applications response to find an agent the current user has already liked
            # Per AFS precondition: "An agent card is already liked by the current user"
            liked_app = agent_hub.find_liked_application(applications)
            assert liked_app is not None, (
                "Test precondition not met: no agent card is currently liked by the user. "
                "The AFS precondition requires an agent with data-liked='true' to exist. "
                "Please like an agent first and retry."
            )

            liked_agent_id = liked_app["id"]
            initial_like_count = liked_app.get("likes", 0)
            logger.info(
                "Found pre-existing liked agent: id=%s, initial_count=%s",
                liked_agent_id,
                initial_like_count,
            )

        with allure.step("Step 2a — Verify the agent card is visible and liked"):
            assert liked_agent_id is not None, "No liked agent could be located or created"
            like_button = page.locator(f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]')
            assert like_button.count() > 0, f"Like button for agent {liked_agent_id} should be visible"
            data_liked = like_button.get_attribute("data-liked")
            assert data_liked == "true", (
                f"Expected agent {liked_agent_id} to have data-liked='true', got '{data_liked}'"
            )
            logger.info("Agent %s is ready for unlike test (data-liked='true', count=%s)",
                       liked_agent_id, initial_like_count)

        with allure.step("Step 3 — Click the heart icon (like button) on the agent card to unlike it"):
            like_button = page.locator(f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]')
            console_errors = agent_hub.capture_console_errors()

            assert like_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                f"Like button for agent {liked_agent_id} should be visible"
            )
            response = agent_hub.click_like_button(liked_agent_id, timeout=UI_ELEMENT_TIMEOUT)
            # Response should be 204 No Content for DELETE /social/like/...
            assert response.status in (201, 204), (
                f"Expected DELETE .../social/like/... to return 201 or 204, got {response.status}"
            )
            logger.info("Unlike button click response: %s", response.status)

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
            # Soft-assert on unexpected errors — don't fail hard, collect them
            if unexpected_errors:
                soft_failures.append(
                    f"Unexpected console errors on unlike click: {unexpected_errors}"
                )
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
                # Agent card still visible in the default view (Trending top-6 or default list)
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
                # Agent not in default view; verify via search box per AFS § Step 6
                logger.info(
                    "Agent %s not in default view after refresh; verifying via search box",
                    liked_agent_id,
                )
                # Search for the agent by ID (converted to string for matching)
                # Note: searching by agent ID directly; the agent name is dynamic user-authored content
                # Per AFS: "locate the SAME agent (dynamically via data-testid if still rendered in
                # default view, or via search box if not)"
                agent_hub.search(str(liked_agent_id), timeout=UI_ELEMENT_TIMEOUT)
                page.wait_for_timeout(1000)

                # Check if the agent appears in search results
                search_result_buttons = page.locator(
                    f'[data-testid="catalog-agent-like-button-{liked_agent_id}"]'
                )
                assert search_result_buttons.count() > 0, (
                    f"Agent {liked_agent_id} should appear in search results after refresh"
                )

                # Verify the state is still unliked
                data_liked_search = search_result_buttons.first.get_attribute("data-liked")
                like_count_search_text = (search_result_buttons.first.text_content() or "0").strip()
                like_count_search = int(like_count_search_text)

                assert data_liked_search == "false", (
                    f"After refresh (search verification): expected data-liked='false', got '{data_liked_search}'"
                )
                assert like_count_search == new_like_count, (
                    f"After refresh (search verification): expected like count {new_like_count}, "
                    f"got {like_count_search}"
                )
                logger.info(
                    "Like state persisted after refresh (via search): data-liked='false', count=%s",
                    like_count_search,
                )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
