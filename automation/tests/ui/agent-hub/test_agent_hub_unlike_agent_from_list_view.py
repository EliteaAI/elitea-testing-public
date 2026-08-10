"""UI Test for ELITEA-2355 — Agent Hub: unlike an agent from the list view.

Verifies that unliking a liked agent card on the Agent Hub (Catalog) page
(`/elitea-catalog`) decrements its like count, empties the heart icon to its
inactive state, and both persist across a full page refresh.

Unlike ELITEA-2354 (like), this case does NOT re-like at the end because the
unlike operation IS the intended final state. The count stays 0, the agent stays
unliked — this is correct cleanup per the AFS § Cleanup.

Spec: test-specs/agent-hub/l3_agent-hub-unlike-agent-from-list-view_ELITEA-2355.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup
(ELITEA-2075) plus the like-button helpers added by ELITEA-2354; no new
page-object changes.

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time. Functionally
harmless — the like/unlike flow itself (count, icon, persistence, backend call)
is entirely correct. Soft-asserted via the pytest-native `soft_failures`/
`pytest.fail()` mechanism so this stays a tracked, visible RED until the fix
ships, without masking a genuinely new console error. Sanctioned-RED per
`.agents/testing.md` § Merge gate.

Usage:
    cd automation
    pytest tests/ui/agent-hub/test_agent_hub_unlike_agent_from_list_view.py -v
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

_KNOWN_DEFECT_1215_PREFIX = (
    "A non-serializable value was detected in an action, in the path: `payload.updateFn`"
)


def _is_known_defect_1215(text: str) -> bool:
    """True for the known, filed, non-blocking Redux console error
    (EliteaAI/elitea-testing-public#1215) that fires on every like/unlike
    click on an Agent Hub agent card. Matches on the warning's own stable
    text prefix (the exact reducer-value suffix varies per click/agent, so
    it is not part of the match).
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
    @pytest.mark.p2
    def test_agent_hub_unlike_agent_from_list_view(self, page: Page):
        """Unliking a liked agent card decrements its count, empties the heart
        icon, and persists across a full page refresh. Final state: count 0,
        unliked (no re-like cleanup unlike ELITEA-2354).

        Approach (mirrors ELITEA-2354 in reverse): Finds an unliked agent,
        likes it as a setup step, then tests the unlike flow. Unlike ELITEA-2354
        which re-likes for cleanup, this test leaves the agent unliked (the
        final state) as its cleanup, so no re-like is performed.
        """
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []
        liked_for_test = False
        application_id: int | None = None
        agent_name: str | None = None

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step("Setup — Find an unliked agent and like it (precondition for test)"):
                target = agent_hub.find_unliked_application(applications)
                assert target is not None, (
                    "Expected at least one published agent NOT liked by the current user at test start "
                    "(dynamic discovery — live like states are mutable shared product data)"
                )
                application_id = target["id"]
                agent_name = target["name"]

                # Verify not liked at start
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should not be liked at test start"
                )

                # Like the agent (setup for this test's precondition)
                setup_response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                assert setup_response.status == 201, (
                    f"Setup like failed: expected 201, got {setup_response.status}"
                )
                # Wait for count to update (optimistic client-side update)
                agent_hub.wait_for_like_count(application_id, 1, timeout=UI_ELEMENT_TIMEOUT)
                liked_for_test = True

            with allure.step(f"Step 2 — Locate the liked agent card ({agent_name!r}, just liked in setup)"):
                # Search for the agent to ensure it's visible and navigated to
                agent_hub.search(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} (id={application_id}) should be visible after liking"
                )
                # Double-check the liked state is visible
                assert agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} should show data-liked='true' after setup like"
                )

            with allure.step(f"Step 3 — Click the heart icon on {agent_name!r} (unlike)"):
                console_errors = agent_hub.capture_console_errors()
                response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                assert response.status == 204, (
                    f"Expected DELETE .../social/like/... to return 204, got {response.status}"
                )

            with allure.step("Step 4 — Verify the like count decrements by 1"):
                # Wait for count update first (optimistic client-side update, same as Step 5 in ELITEA-2354)
                agent_hub.wait_for_like_count(application_id, 0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Verify the heart icon changes to an unfilled/inactive state"):
                # After waiting for count (which pumps the event loop), check the state
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should show data-liked='false' after unliking"
                )

            with allure.step(
                "Side-channel check — known defect #1215 console error on the unlike click"
            ):
                unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
                assert not unexpected_errors, f"Unexpected console errors on unlike click: {unexpected_errors}"
                known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                        f"non-serializable Redux console error(s) on unlike click: {len(known_defect_errors)} "
                        "occurrence(s)"
                    )
                console_errors.stop()

            with allure.step(
                "Step 6 — Refresh the page and verify the updated like count and unliked state persist"
            ):
                page.reload()
                agent_hub.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                # Re-locate via search since post-refresh view may not show low-count agents
                agent_hub.search(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} should be visible via search after refresh"
                )
                agent_hub.wait_for_like_count(application_id, 0, timeout=UI_ELEMENT_TIMEOUT)
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should still show data-liked='false' after refresh"
                )

        finally:
            # NOTE: Unlike ELITEA-2354, this case does NOT cleanup-re-like.
            # The unlike operation IS the intended final state (AFS § Cleanup).
            # Leaving it unliked (count 0) is correct and clean for other cases.
            pass

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
