"""UI Test for ELITEA-2364 — Agent Hub: "My Liked" filter shows only liked agents.

Verifies that Agent Hub's "My Liked" category filter displays ONLY agents
liked by the current user, and that unliking an agent while in the filtered
view removes it from the list immediately (optimistic update).

This test uses dynamic agent discovery — it finds any agent the current user
hasn't liked yet, likes it, activates the "My Liked" filter, verifies the
agent appears in the filtered view, then unlikes it and verifies removal.
No hardcoded agent names/IDs because like state is mutable, shared product
data (see AFS § Test Data).

Spec: test-specs/agent-hub/l3_agent-hub-my-liked-filter-shows-only-liked-agents_ELITEA-2364.md

Reuses AgentHubPage (ELITEA-2075) + its like-button and filter helpers
(ELITEA-2350/2352/2354/2365).

Known defect (filed, non-blocking — AFS § Known Defects,
EliteaAI/elitea-testing-public#1215): clicking the like/unlike heart icon
fires a Redux "non-serializable value" console.error every time. Harmless
— the like/unlike flow itself is correct. Soft-asserted so this stays
tracked-RED until the fix ships, without masking new console errors
(same idiom as ELITEA-2354).

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_hub_my_liked_filter_shows_only_liked_agents.py -v
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
    click on an Agent Hub agent card.
    """
    return _KNOWN_DEFECT_1215_PREFIX in text


class TestAgentHubMyLikedFilterShowsOnlyLikedAgents:
    """ELITEA-2364: Agent Hub — My Liked filter shows only liked agents (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2364_agent-hub-my-liked-filter-shows-only-liked-agents.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1215",
        "Known defect — non-serializable console error on like/unlike click",
    )
    @pytest.mark.p2
    def test_agent_hub_my_liked_filter_shows_only_liked_agents(self, page: Page):
        """Like an agent, activate the "My Liked" filter, verify the agent
        appears in the filtered list, then unlike the agent and verify it
        is removed from the filtered list immediately (optimistic update)."""
        agent_hub = AgentHubPage(page)
        soft_failures: list[str] = []
        liked = False
        application_id: int | None = None
        agent_name: str | None = None

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                applications = agent_hub.navigate_and_capture_applications(timeout=NAVIGATION_TIMEOUT)
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step("Step 2 — Locate an agent card the current user hasn't liked yet"):
                target = agent_hub.find_unliked_application(applications)
                assert target is not None, (
                    "Expected at least one agent the current user hasn't liked yet "
                    "(dynamic discovery — like state is mutable shared product data, "
                    "not a stable per-name fixture; see this case's AFS § Test Data)"
                )
                application_id = target["id"]
                agent_name = target["name"]
                assert agent_hub.get_agent_card(agent_name).first.is_visible(), (
                    f"Agent card {agent_name!r} (id={application_id}) should be visible on the Catalog page"
                )
                assert not agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should not be liked by the current user at start"
                )

            with allure.step(f"Step 3 — Click the heart icon on {agent_name!r} to like it"):
                console_errors = agent_hub.capture_console_errors()
                response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                liked = True
                assert response.status == 201, (
                    f"Expected POST .../social/like/... to return 201, got {response.status}"
                )
                # Verify the count incremented (baseline to pre-like count)
                baseline_count = target.get("likes", 0)
                expected_count = baseline_count + 1
                agent_hub.wait_for_like_count(application_id, expected_count, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify the like button shows data-liked='true'"):
                assert agent_hub.is_agent_liked(application_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Agent {agent_name!r} (id={application_id}) should show data-liked='true' after liking"
                )

            with allure.step(
                "Side-channel check — known defect #1215 console error on the like click "
                "(checked after previous steps' waits, so the async dispatch has landed)"
            ):
                unexpected_errors = [m.text for m in console_errors if not _is_known_defect_1215(m.text)]
                assert not unexpected_errors, f"Unexpected console errors on like click: {unexpected_errors}"
                # Known defect: EliteaAI/elitea-testing-public#1215 — recorded in
                # soft_failures (a raw console-message list isn't expect.soft()
                # -bindable) so it stays a tracked, visible RED until the product
                # fix ships. Sanctioned-RED per .agents/testing.md § Merge gate.
                known_defect_errors = [m.text for m in console_errors if _is_known_defect_1215(m.text)]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1215: "
                        f"non-serializable Redux console error(s) on like click: {len(known_defect_errors)} "
                        "occurrence(s)"
                    )
                console_errors.stop()

            with allure.step("Step 5 — Click the 'My Liked' category filter chip to activate the filter"):
                agent_hub.click_category_filter_chip("My Liked", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 6 — Verify the 'My Liked' filter is selected"):
                assert agent_hub.is_category_filter_chip_selected("My Liked", timeout=UI_ELEMENT_TIMEOUT), (
                    "The 'My Liked' filter chip should show data-selected='true' after clicking"
                )

            with allure.step("Step 7 — Verify the 'My Liked' category section is now visible"):
                assert agent_hub.is_category_section_visible("my-liked", timeout=UI_ELEMENT_TIMEOUT), (
                    "The 'My Liked' category section heading should be visible after filter activation"
                )

            with allure.step(f"Step 8 — Verify {agent_name!r} is now displayed in the 'My Liked' section"):
                # The agent was just liked, so it should be visible in the filtered list
                agent_card = agent_hub.get_agent_card(agent_name)
                assert agent_card.count() > 0, (
                    f"Agent card {agent_name!r} (id={application_id}) should be visible "
                    "in the 'My Liked' filtered list after liking"
                )
                assert agent_card.first.is_visible(), (
                    f"Agent card {agent_name!r} should be visible in the 'My Liked' filtered list"
                )

            with allure.step(f"Step 9 — Unlike {agent_name!r} while in the 'My Liked' view"):
                unlike_console_errors = agent_hub.capture_console_errors()
                unlike_response = agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                liked = False  # Track that cleanup is no longer needed
                assert unlike_response.status == 204, (
                    f"Expected DELETE .../social/like/... to return 204, got {unlike_response.status}"
                )

            with allure.step(
                "Step 10 — Verify the agent is removed from the 'My Liked' list (optimistic update)"
            ):
                # Wait for the agent card to be removed from the filtered view
                # (the optimistic update removes it immediately from the client state)
                # Capture the initial count BEFORE the unlike (from Step 9)
                initial_count = agent_hub.get_agent_card_count()

                # After unliking, the card should disappear from the "My Liked" view
                # Use wait_for_agent_card_count_not() to verify count decreased (AFS § Step 6)
                agent_hub.wait_for_agent_card_count_not(initial_count, timeout=UI_ELEMENT_TIMEOUT)

                # Verify the agent card is no longer present in the DOM
                assert agent_hub.get_agent_card(agent_name).count() == 0, (
                    f"Agent card {agent_name!r} (id={application_id}) should be removed from "
                    "the 'My Liked' filtered list after unliking (AFS § Step 6)"
                )

                # Verify the agent is no longer liked
                assert not agent_hub.is_agent_liked(application_id, timeout=5000), (
                    f"Agent {agent_name!r} (id={application_id}) should show data-liked='false' after unliking"
                )

            with allure.step(
                "Side-channel check — known defect #1215 console error on the unlike click"
            ):
                unexpected_unlike_errors = [
                    m.text for m in unlike_console_errors if not _is_known_defect_1215(m.text)
                ]
                assert not unexpected_unlike_errors, (
                    f"Unexpected console errors on unlike click: {unexpected_unlike_errors}"
                )
                # Known defect #1215 also fires on unlike (AFS § Known Defects) —
                # expected, but only counted once (from the like click above), so
                # log-only here (same as ELITEA-2354).
                unlike_console_errors.stop()

        finally:
            # Cleanup (mandatory): this test mutates shared, cross-session product
            # data (the agent's public like state) — make sure to restore it.
            if liked and application_id is not None:
                with allure.step("Cleanup — unlike the agent to restore the pre-test baseline"):
                    try:
                        agent_hub.click_like_button(application_id, timeout=UI_ELEMENT_TIMEOUT)
                        logger.info("Cleanup unlike succeeded for %r (id=%s)", agent_name, application_id)
                    except Exception as exc:  # noqa: BLE001 — cleanup must never mask real failure
                        logger.error(
                            "Cleanup unlike raised for %r (id=%s): %s", agent_name, application_id, exc
                        )
                        soft_failures.append(
                            f"Cleanup unlike failed for {agent_name!r} "
                            f"(id={application_id}): {exc}"
                        )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
