"""UI test — agent cannot be added to its own toolkit picker (ELITEA-1887).

Verifies that the current agent never appears among its own "+ Agent" picker
search results — self-attachment is blocked — both in the unfiltered
(initial) list and when searching by the agent's own exact name.

Reuses existing project data (no generate-per-test entities): the seeded
"Test Agent" (id 3), same agent reused by the ELITEA-1950 AFS. Pure
read/search flow — creates no persistent entity, mutates no state, needs no
cleanup.

Per the reverse-masking guard, this test asserts the live-accurate target
rather than the case's stale text: the case's steps 2-3 say to click "+
Toolkit" and search there, but the live product's Tools section has four
independent add buttons (Toolkit / MCP / Agent / Pipeline) and only the
"+ Agent" button's popper lists other agents that could be attached as a
sub-agent tool — the "+ Toolkit" popper lists Toolkit-type entities only and
is unrelated to agent self-attachment. See the case-text-drift
CLARIFICATION posted as a work-log comment on
https://github.com/EliteaAI/elitea-testing-public/issues/133.

Load-bearing technical detail (see AFS § Network Behavior): the backend does
NOT filter the current agent out of its own search results — the API
response for the debounced search actually includes the self-agent row.
Self-exclusion is enforced entirely client-side
(`EliteaUI/src/pages/Applications/Components/Tools/ToolMenu.jsx:401`). This
test therefore asserts DOM-level menu-item absence (no `role="menuitem"`
with the agent's own accessible name), never network-response emptiness —
asserting against the API response would test the wrong contract.

No product defect found.

Spec: test-specs/agents/l2_agent-cannot-be-added-to-own-toolkit-picker_ELITEA-1887.md
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.agents")

# reuse-existing per AFS Test Data — no generate-per-test entities created.
AGENT_ID = 3  # seeded "Test Agent"
AGENT_NAME = "Test Agent"


class TestAgentSelfAttachmentBlocked:
    """Agent Cannot Be Added to Its Own Toolkit Picker (ELITEA-1887, l2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/agents/"
        "ELITEA-1887_agent-cannot-be-added-to-its-own-toolkit-picker.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_agent_self_attachment_blocked(self, page):
        """Current agent never appears in its own "+ Agent" picker results.

        Steps (AFS test-specs/agents/l2_agent-cannot-be-added-to-own-toolkit-
        picker_ELITEA-1887.md):
        1. Navigate to the agent detail page.
        2. Open the "+ Agent" picker (live-accurate equivalent of the case's
           "+ Toolkit" — see module docstring); verify the current agent is
           absent from the initial, unfiltered list.
        3. Search the picker for the current agent's own exact name; verify
           the debounced search request fires and returns 200.
        4. Verify the current agent is still absent from the rendered menu
           items (DOM-level, not network-response-level — see module
           docstring).
        """
        detail_page = AgentDetailPage(page)

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page.navigate(AGENT_ID)
            detail_page.verify_on_detail_page(expected_agent_id=AGENT_ID)
            assert detail_page.get_agent_id() == str(AGENT_ID), (
                f"Information section should show Agent ID {AGENT_ID}"
            )
            assert detail_page.get_name() == AGENT_NAME, (
                f"General section should show Name {AGENT_NAME!r}"
            )

        with allure.step(
            "Step 2 — Open the '+ Agent' picker (live-accurate equivalent of "
            "the case's '+ Toolkit' — see module docstring); current agent "
            "is absent from the unfiltered initial list"
        ):
            popper = detail_page.open_agent_picker(timeout=UI_ELEMENT_TIMEOUT)
            expect(
                detail_page.get_agent_picker_menuitem(popper, AGENT_NAME)
            ).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT), (
                f"'{AGENT_NAME}' should not appear in its own unfiltered "
                "agent picker list"
            )

        with allure.step(
            f"Step 3 — Search the picker for the agent's own exact name "
            f"'{AGENT_NAME}'; debounced search request returns 200"
        ):
            encoded_query = f"query={AGENT_NAME.replace(' ', '+')}"
            # Condition-based wait (not a sleep): block until the specific
            # debounced GET for this exact query resolves, per AFS
            # Automation Hints ("wait_for_response matching
            # /applications/prompt_lib/.*query=<encoded-name>/").
            with page.expect_response(
                lambda resp: "applications/prompt_lib" in resp.url
                and encoded_query in resp.url,
                timeout=UI_ELEMENT_TIMEOUT,
            ) as response_info:
                detail_page.search_agent_picker(popper, AGENT_NAME)
            search_response = response_info.value
            assert search_response.status == 200, (
                f"Expected the '{AGENT_NAME}' search request "
                f"({search_response.url}) to return 200, got "
                f"{search_response.status}"
            )

        with allure.step(
            "Step 4 — Current agent is still absent from the rendered menu "
            "items after searching its own name (DOM-level, not "
            "network-response-level — see module docstring)"
        ):
            expect(
                detail_page.get_agent_picker_menuitem(popper, AGENT_NAME)
            ).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT), (
                f"'{AGENT_NAME}' should not appear in its own agent picker "
                "search results, even when searching its exact own name"
            )

        assert not console_errors, (
            "Expected no console errors from the agent-picker search flow, "
            f"got: {[m.text for m in console_errors]}"
        )
