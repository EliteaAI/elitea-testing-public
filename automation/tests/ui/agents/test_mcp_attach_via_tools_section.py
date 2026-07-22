"""UI test — attach a Remote MCP to an agent via the Tools section (ELITEA-1950).

Verifies that a Remote MCP toolkit can be attached to an agent from the Tools
section's "+ MCP" add button, persists across a full page reload, and can be
removed via the shared toolkit-card delete flow — persistence confirmed both
ways via a fresh reload.

Uses fixtures to create fresh test data per run:
- ``agent_id``: Creates and cleans up a fresh agent
- ``mcp_toolkit_with_tools``: Creates and cleans up a fresh Remote MCP toolkit

Per the reverse-masking guard, this test asserts the live product's contract
rather than the case's stale text: the case describes "tool type tabs" with
an "active tab" state and an explicit agent-level Save step; the live product
instead renders four independent "+ <Type>" add buttons (no tabs, no active
state) and auto-saves the MCP attachment immediately on selection (no Save
click). See the case-text-drift CLARIFICATION:
https://github.com/EliteaAI/elitea-testing-public/issues/530

Two Axis-2 additions from the AFS are scoped down in this implementation
because their only available handles are text-based (no data-testid exists
and none may be added in this PR — the testid-only, no-fallback locator
policy forbids a text/tooltip-based locator, and this dispatch's `automation/
testids` integration branch is sealed to the analyst's already-merged
`agent-add-mcp-button` commit):
- Case step 3's "4 tabs" is asserted only for the two testid-backed buttons
  (Toolkit, MCP) — the Agent/Pipeline add buttons in `ToolMenu.jsx` carry no
  `data-testid` and are out of scope to add here.
- The attached MCP card's disconnected-status tooltip + "Log in" button
  (`ToolCard.jsx`'s `McpLogInButton` / status icon `Tooltip`) also carry no
  `data-testid`. Not asserted; flagged as a follow-up in the AFS.

No product defect found.

Spec: test-specs/agents/l3_mcp-attach-via-tools-section_ELITEA-1950.md
"""

import logging

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.mcp]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.agents")


class TestMcpAttachViaToolsSection:
    """Attach MCP via Tools Section (ELITEA-1950, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/mcp/"
        "ELITEA-1950_mcp-integration-in-agent-attach-mcp-via-tools-section.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_mcp_attach_via_tools_section(self, page, agent_id, mcp_toolkit_with_tools):
        """Attach a Remote MCP to an agent, verify persistence across reload,
        then remove it and verify removal persists too.

        Steps (AFS test-specs/agents/l3_mcp-attach-via-tools-section_ELITEA-1950.md):
        1. Navigate to the agent detail page.
        2. Verify the Tools section is expanded.
        3. Verify the Toolkit/MCP add buttons are visible (live-accurate
           equivalent of the case's "tool type tabs" — see module docstring).
        4. Click "+ MCP"; the shared popper opens with search + menu items.
        5. Select the target MCP by name.
        6. Verify the MCP appears as a card in the Tools section.
        7. Verify the attach auto-saves (PATCH .../tool/prompt_lib/... -> 201;
           no separate agent-level Save step exists for this flow).
        8. Reload; verify the MCP is still attached.
        9. Remove the MCP; confirm the "Remove MCP?" dialog; verify it's gone,
           including after a fresh reload.

        Args:
            page: Playwright page fixture.
            agent_id: Fresh agent created by fixture (auto-cleanup).
            mcp_toolkit_with_tools: Fresh MCP toolkit created by fixture (auto-cleanup).
        """
        mcp_name = mcp_toolkit_with_tools["name"]
        detail_page = AgentDetailPage(page)

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        # Capture the auto-save PATCH traffic so Step 7 can assert on the
        # real persistence signal (201), not only a UI-visible toast.
        tool_requests = detail_page.capture_requests_matching(
            "tool/prompt_lib", method="PATCH"
        )

        try:
            with allure.step("Step 1 — Navigate to agent detail page"):
                detail_page.navigate(agent_id)
                detail_page.verify_on_detail_page(expected_agent_id=agent_id)
                assert detail_page.get_agent_id() == str(agent_id), (
                    f"Information section should show Agent ID {agent_id}"
                )

            with allure.step("Step 2 — Tools section is visible and expanded"):
                detail_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.toolkits_section.is_visible(), (
                    "Tools section should be expanded by default"
                )

            with allure.step(
                "Step 3 — Toolkit/MCP add buttons are visible (live-accurate "
                "equivalent of the case's 'tool type tabs' — see module docstring)"
            ):
                assert detail_page.add_toolkit_button.is_visible(), (
                    "'+ Toolkit' add button should be visible in the Tools section"
                )
                assert detail_page.add_mcp_button.is_visible(), (
                    "'+ MCP' add button should be visible in the Tools section"
                )

            with allure.step(
                f"Step 4/5 — Click '+ MCP', select '{mcp_name}' from the popper"
            ):
                assert not detail_page.is_toolkit_attached(mcp_name, timeout=1000), (
                    f"MCP '{mcp_name}' should not be attached before the attach action"
                )
                detail_page.add_mcp(mcp_name)

            with allure.step("Step 6 — MCP appears as a card in the Tools section"):
                assert detail_page.is_toolkit_attached(mcp_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"MCP card for '{mcp_name}' should render after attaching"
                )

            with allure.step(
                "Step 7 — Attach auto-saves via PATCH .../tool/prompt_lib/... "
                "-> 201 (no separate agent-level Save step for this flow)"
            ):
                attach_calls = [
                    req for req in tool_requests if req["status"] == 201
                ]
                assert attach_calls, (
                    "At least one PATCH .../tool/prompt_lib/... request should "
                    f"have returned 201 on MCP attach, captured: {tool_requests!r}"
                )

            with allure.step("Step 8 — Reload; MCP is still attached"):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.is_toolkit_attached(mcp_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"MCP '{mcp_name}' should still be attached after a full page reload"
                )

            with allure.step(
                "Step 9 — Remove the MCP attachment; confirm the 'Remove MCP?' "
                "dialog; verify it's gone, including after a fresh reload"
            ):
                detail_page.remove_mcp(mcp_name)
                assert not detail_page.is_toolkit_attached(mcp_name, timeout=3000), (
                    f"MCP card for '{mcp_name}' should no longer render after removal"
                )

                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert not detail_page.is_toolkit_attached(mcp_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"MCP '{mcp_name}' should remain detached after a fresh reload — "
                    "removal must have persisted server-side"
                )

            assert not console_errors, (
                "Expected no console errors from the attach/detach flow, got: "
                f"{[m.text for m in console_errors]}"
            )

        finally:
            # Cleanup: detach MCP if still attached (fixtures handle entity deletion)
            try:
                if detail_page.is_toolkit_attached(mcp_name, timeout=2000):
                    detail_page.remove_mcp(mcp_name)
                    logger.info(
                        "Cleanup: detached MCP %r from agent %d", mcp_name, agent_id,
                    )
            except Exception as exc:
                logger.warning(
                    "Cleanup: failed to confirm/detach MCP %r from agent %d: %s",
                    mcp_name, agent_id, exc,
                )
