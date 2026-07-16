"""UI Test for agent detail Back-button navigation (ELITEA-1869).

Verifies that clicking the Back button on an agent detail page returns the
user to the Agents dashboard with the list intact (same agents, same order,
same count), rather than redirecting to Chat or another page.

Spec: test-specs/agents/l1_agent-detail-back-navigation-returns-to-agents-list_ELITEA-1869.md

Uses a pre-existing agent from the project's Agents list (read-only) instead
of the ``agent_id`` fixture: that fixture unconditionally calls
``AgentAPI.create_agent()``, which currently 400s against the DEV backend
(open defect https://github.com/EliteaAI/elitea-testing-public/issues/524 —
temperature/reasoning_effort conflict). This case's precondition only
requires an *existing* agent, so the first card on the dashboard is reused
instead — no agent is created, edited, or deleted; nothing to clean up.

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p1: high priority (frontmatter priority is "critical"/l1; marked p1 as
      the closest existing marker — no p0-vs-p1 distinction is drawn in this
      AFS beyond "critical", and p1 is the project's convention for
      non-smoke regression coverage of a critical-but-non-blocking flow)
"""

import allure
import pytest

from pages.agent_page import AgentPage
from pages.agents_list_page import AgentsListPage
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

NAVIGATION_TIMEOUT = 15000


@pytest.mark.p1
@pytest.mark.regression
def test_back_button_from_agent_detail_returns_to_intact_agents_list(page):
    """Back button on agent detail page returns to Agents dashboard with
    the list intact (ELITEA-1869).

    Uses the first pre-existing agent card on the dashboard — read-only,
    no test data created or cleaned up.
    """
    agent = AgentPage(page)
    list_page = AgentsListPage(page)
    detail_page = AgentDetailPage(page)

    console_messages = []
    page.on(
        "console",
        lambda msg: console_messages.append(msg) if msg.type == "error" else None,
    )

    with allure.step("Step 1 — Navigate to the Agents page"):
        agent.navigate_to_agents()
        agents_before = agent.get_agent_card_names(timeout=NAVIGATION_TIMEOUT)
        assert agents_before, (
            "Precondition: at least one agent must exist in the project's "
            "Agents list for this case to be exercised"
        )

    with allure.step("Step 2 — Click into an existing agent card to open its detail page"):
        target_agent_name = agents_before[0]
        agent.select_agent_from_list(target_agent_name)
        detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        assert "/agents/all/" in page.url, (
            f"Expected to land on an agent detail route after selecting "
            f"'{target_agent_name}', got: {page.url}"
        )

    with allure.step("Step 3 — Click the Back button in the agent detail page header"):
        with page.expect_response(
            lambda r: "applications/prompt_lib/" in r.url and "agents_type=classic" in r.url
        ):
            agent.click_back_button(timeout=NAVIGATION_TIMEOUT)
        assert page.url.rstrip("/").endswith("/agents/all?viewMode=owner"), (
            f"Back navigation should return to the Agents list route "
            f"(/agents/all?viewMode=owner), got: {page.url}"
        )

    with allure.step("Step 4 — Verify the Agents dashboard is shown"):
        list_page.verify_dashboard_header_visible()

    with allure.step(
        "Step 5 — Verify the list is intact: same agents, same order, same "
        "count as before navigating into the detail page (not just non-empty)"
    ):
        agents_after = agent.get_agent_card_names(timeout=NAVIGATION_TIMEOUT)
        assert agents_after == agents_before, (
            "Agents list after Back navigation should exactly match the "
            f"pre-navigation list (order + count). Before: {agents_before}, "
            f"after: {agents_after}"
        )

    with allure.step(
        "Side-channel check — no console errors across the navigate → "
        "detail → back flow"
    ):
        assert not console_messages, (
            "Unexpected console errors during Back navigation: "
            f"{[m.text for m in console_messages]}"
        )
