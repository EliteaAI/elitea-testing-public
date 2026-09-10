"""UI Test for agent detail back-navigation (ELITEA-1869).

Verifies that using the agent detail page's header navigation control returns
the user to the Agents dashboard with the list intact (same agents, same
order, same count), rather than redirecting to Chat or another page.

**Adjustment (2026-09-10).** EliteaAI/EliteaUI@f1d4ea47 (EL-6460) replaced the
detail page's standalone back-arrow with a breadcrumb trail: on
``/agents/:tab/:agentId`` ``BreadcrumbsOrTitle`` always takes the
``<Breadcrumbs/>`` branch, so ``data-testid="back-button"`` never mounts there.
The go-back control is now the ancestor crumb labelled "Agents". Intentional UI
drift, no product defect — see the AFS's § Adjustment. Every case-level
expected result is preserved; the legacy control's *absence* is now asserted so
a future restoration of the arrow turns this test red instead of the drift
rotting in a comment.

Spec: test-specs/agents/l1_agent-detail-back-navigation-returns-to-agents-list_ELITEA-1869.md

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p0: critical priority (frontmatter priority is "critical"/l1 —
      matches pytest.ini's p0 marker, the project's convention for
      must-pass-for-deploy coverage)
"""

import re
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_page import AgentPage
from pages.agents_list_page import AgentsListPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

pytestmark = [pytest.mark.ui, pytest.mark.agents]

NAVIGATION_TIMEOUT = 15000


@pytest.mark.p0
@pytest.mark.regression
def test_back_button_from_agent_detail_returns_to_intact_agents_list(page):
    """The agent detail page's breadcrumb back-navigation returns to the
    Agents dashboard with the list intact (ELITEA-1869).

    Read-only: reuses whichever agent already sits first in the project's
    Agents list, creates nothing and cleans nothing up. The ``agent_id``
    fixture is deliberately NOT used — the test clicks the first card, never
    that agent, and every invocation would pay an ``agent_api.create_agent``
    that walks into open defect #524.

    The arrival at the detail page is an in-app card click, never a
    ``page.goto`` deep link: for a back-navigation case the arrival path is
    part of what produces the observable (.agents/testing.md § Fidelity policy
    / the ELITEA-2022 wrong-interface-precondition entry).
    """
    agent = AgentPage(page)
    list_page = AgentsListPage(page)
    detail_page = AgentDetailPage(page)

    console_errors = collect_console_errors(page)

    with allure.step("Step 1 — Navigate to the Agents page"):
        agent.navigate_to_agents()
        list_page.verify_dashboard_header_visible()
        agents_before = agent.get_agent_card_names(timeout=NAVIGATION_TIMEOUT)
        assert agents_before, (
            "Precondition: at least one agent must exist in the project's "
            "Agents list for this case to be exercised"
        )

    with allure.step("Step 2 — Click into an existing agent card to open its detail page"):
        target_agent_name = agents_before[0]
        list_page.open_first_agent(timeout=NAVIGATION_TIMEOUT)
        detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
        assert "/agents/all/" in page.url, (
            f"Expected to land on an agent detail route after opening "
            f"'{target_agent_name}', got: {page.url}"
        )

    with allure.step(
        "Step 3a — The legacy back-arrow control is not rendered on the "
        "agent detail route (EliteaAI/EliteaUI@f1d4ea47)"
    ):
        # First-class, deliberate absence assertion: if the UI team restores
        # the arrow, this test goes red and the TMS case text gets revisited.
        expect(detail_page.back_button).to_have_count(0)

    with allure.step(
        "Step 3b — The breadcrumb trail is the replacement go-back affordance"
    ):
        expect(detail_page.breadcrumbs_nav).to_be_visible()
        expect(detail_page.breadcrumbs_nav).to_have_text(
            re.compile(rf"^Agents\s*/\s*{re.escape(target_agent_name)}$")
        )
        # Count-then-text, not a bare `.first`: exactly one ancestor crumb
        # renders here today, and asserting the count makes that an enforced
        # invariant rather than a silent assumption.
        expect(detail_page.breadcrumb_parent_link).to_have_count(1)
        expect(detail_page.breadcrumb_parent_link).to_have_text("Agents")
        expect(detail_page.detail_title).to_have_text(target_agent_name)
        expect(detail_page.detail_title).to_have_attribute("aria-current", "page")

    with allure.step(
        "Step 3c/3d — Click the 'Agents' breadcrumb and land back on the "
        "Agents list route"
    ):
        with page.expect_response(
            lambda r: "applications/prompt_lib/" in r.url and "agents_type=classic" in r.url
        ):
            detail_page.click_breadcrumb_parent(timeout=NAVIGATION_TIMEOUT)

        landing_url = page.url
        landing = urlparse(landing_url)
        assert landing.path.rstrip("/").endswith("/agents/all"), (
            "Breadcrumb back-navigation should return to the Agents list "
            f"route (/agents/all), got path: {landing.path!r} "
            f"(full URL: {landing_url})"
        )
        assert parse_qs(landing.query).get("viewMode") == ["owner"], (
            "The Agents list route should be entered with viewMode=owner, "
            f"got query: {landing.query!r}"
        )
        # The case's own Fail criterion: redirected elsewhere = FAIL.
        assert "/chat" not in landing_url, (
            f"Back navigation must not redirect to Chat, got: {landing_url}"
        )

    with allure.step("Step 4 — Verify the Agents dashboard is shown"):
        list_page.verify_dashboard_header_visible()

    with allure.step(
        "Step 5 — Verify the list is intact: same agents, same order, same "
        "count as before navigating into the detail page (not just non-empty)"
    ):
        # Mandatory, and loud on purpose: `get_agent_card_names` swallows its
        # own card wait and returns [] on timeout, and networkidle races the
        # persistent /socket.io/ polling transport (#1847), so without this
        # the read can return an empty list while the header is already
        # visible (AFS § Robustness fixes 1). Wait on what the caller needs.
        list_page.entity_card_name.first.wait_for(
            state="visible", timeout=NAVIGATION_TIMEOUT
        )
        agents_after = agent.get_agent_card_names(timeout=NAVIGATION_TIMEOUT)
        assert agents_after == agents_before, (
            "Agents list after back navigation should exactly match the "
            f"pre-navigation list (order + count). Before: {agents_before}, "
            f"after: {agents_after}"
        )

    with allure.step(
        "Side-channel check — no console errors across the navigate → "
        "detail → breadcrumb-back flow"
    ):
        assert not console_errors, (
            f"Unexpected console errors during back navigation: {console_errors}"
        )
