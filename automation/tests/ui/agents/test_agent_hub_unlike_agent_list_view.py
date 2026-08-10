"""UI Test for ELITEA-2355 — Agent Hub: unlike an agent from the list view.

Verifies that unliking a liked agent card on the Agent Hub (Catalog) page
(`/elitea-catalog`) decrements its like count, unfills the heart icon to its
inactive state, and both persist across a full page refresh. Unlike the
sibling like case (ELITEA-2354), no cleanup is performed — the unlike IS the
meaningful state change the case verifies, and leaving the agent unliked is
the correct final state.

Spec: test-specs/agent-hub/l3_agent-hub-unlike-agent-from-list-view_ELITEA-2355.md

Reuses `AgentHubPage` from ELITEA-2354, extending it with a method to find
a liked application at runtime (`find_liked_application`). The like-button
click/count/state mechanics are identical to ELITEA-2354; only the discovery
and cleanup direction differ.

Known defect (filed, non-blocking — AFS § Known Defects Found,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time
(`agentHub/updateApplicationInCategories` dispatched with a raw function
payload). Functionally harmless — the like/unlike flow itself (count, icon,
persistence, backend call) is entirely correct. Soft-asserted via the
pytest-native `soft_failures`/`pytest.fail()` mechanism (same idiom as
ELITEA-2354 and `test_secret_create_inline_checkmark_x_cancel.py`'s #1203
handling) so this stays a tracked, visible RED until the fix ships, without
masking a genuinely new console error (still hard-fails). Sanctioned-RED per
`.agents/testing.md` § Merge gate.

Testids: The `catalog-agent-like-button-{application.id}` and `data-liked`
state-attribute locators are pre-implemented (ELITEA-2354, already merged).

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
    @pytest.mark.p3
    def test_agent_hub_unlike_agent_from_list_view(self, page: Page):
        """Unliking a liked agent card decrements its count, unfills the heart
        icon, and persists across a full page refresh. No cleanup is needed
        — the unlike is the test's own meaningful action and the final state
        left by the test (unlike ELITEA-2354 which must re-unlike at cleanup)."""
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []
        application_id: int | None = None
        agent_name: str | None = None

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                applications = agent_hub.navigate_and_capture_applications(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step("Step 2 — Locate an agent card currently showing ≥ 1 likes (liked by user)"):
                # Dynamically search for a liked agent in the DOM by checking like buttons
                # This is more reliable than trusting the API response is_liked field
                agent_hub.wait_for_network(timeout=NAVIGATION_TIMEOUT)
                page.wait_for_timeout(500)  # Wait for initial render

                # Look for any like button with data-liked="true"
                liked_like_buttons = page.locator(
                    '[data-testid^="catalog-agent-like-button-"][data-liked="true"]'
                )
                button_count = liked_like_buttons.count()
                assert button_count > 0, (
                    "Expected at least one agent card with data-liked='true' at test start. "
                    "The test requires an agent already liked by the current user. "
                    "(dynamic discovery — live like counts are mutable shared product data)"
                )

                # Get the first liked like button and extract its application ID from the testid
                first_liked_button = liked_like_buttons.first
                testid = first_liked_button.get_attribute("data-testid") or ""
                # testid format: "catalog-agent-like-button-<id>"
                application_id = int(testid.replace("catalog-agent-like-button-", ""))

                # Now find the agent name from the applications response
                target = next((a for a in applications if a["id"] == application_id), None)
                assert target is not None, (
                    f"Agent with id={application_id} not found in applications list"
                )
                agent_name = target["name"]

                # Capture the initial like count for later comparison
                # Use .first to avoid strict mode violations when multiple like buttons exist
                like_button = agent_hub.get_like_button(application_id).first
                like_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                initial_count_text = like_button.text_content() or "0"
                initial_count = int(initial_count_text.strip())
                assert initial_count >= 1, (
                    f"Agent {agent_name!r} (id={application_id}) should have at least 1 like at start, got {initial_count}"
                )

            with allure.step(f"Step 3 — Click the heart icon on {agent_name!r} (unlike)"):
                console_errors = agent_hub.capture_console_errors()
                response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                assert response.status == 204, (
                    f"Expected DELETE .../social/like/... to return 204, got {response.status}"
                )

            with allure.step("Step 4 — Verify the heart icon changes to an unfilled/inactive state"):
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should show data-liked='false' after unliking"
                )

            with allure.step("Step 5 — Verify the like count decrements by 1"):
                # Use wait_for_like_count to ensure the count update has propagated
                # (count updates are optimistic client-side and asynchronous)
                expected_count = initial_count - 1
                agent_hub.wait_for_like_count(application_id, expected_count, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Side-channel check — known defect #1215 console error on the unlike click "
                "(checked here, after steps 4-5's own waits, so the async dispatch that "
                "triggers it has definitely already landed — see this test's module docstring)"
            ):
                unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
                assert not unexpected_errors, f"Unexpected console errors on unlike click: {unexpected_errors}"
                # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
                # soft_failures (a raw console-message list isn't expect.soft()
                # -bindable) so it stays a tracked, visible RED until the product
                # fix ships. Sanctioned-RED per .agents/testing.md § Merge gate.
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
                # The default post-refresh view only renders the top-6 "Trending"
                # cards by like-count descending — an agent that just had a like
                # removed may no longer be in the Trending section, so re-locate
                # via search (same pattern as ELITEA-2354).
                agent_hub.search(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} should be visible via search after refresh"
                )
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should still show data-liked='false' after refresh"
                )
                # Verify the count stayed the same after refresh (no additional mutation)
                agent_hub.wait_for_like_count(application_id, expected_count, timeout=UI_ELEMENT_TIMEOUT)

        finally:
            # No cleanup needed for this case (unlike ELITEA-2354). The unlike
            # IS the meaningful test action, and leaving the agent unliked is
            # the correct final product state.
            pass

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
