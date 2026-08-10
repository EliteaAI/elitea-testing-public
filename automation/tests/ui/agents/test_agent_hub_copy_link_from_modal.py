"""Agent Hub — copy link from agent detail modal navigates to agent (ELITEA-2359).

Verifies that a link copied from the Agent Hub catalog modal's Share action
successfully navigates to the agent and displays all agent details (name,
description, conversation starters, welcome message) correctly in the
reopened modal. The test captures the clipboard-written URL, navigates to it
in a new page context, and confirms the modal auto-opens with the same agent.

Spec: test-specs/agents/l2_copy-link-from-agent-hub-modal-navigates-to-agent_ELITEA-2359.md

Uses existing AgentHubPage locators/methods (modal navigation, modal content
assertions) + new modal-menu / share-link-capture helpers added during this
implementation for the Share menu action and clipboard interception.

Key technical notes (from AFS § Automation Notes & surface.md):
- Clipboard write is captured via monkey-patch `navigator.clipboard.writeText`
  before the Share click, storing the URL into `window.copiedUrl`.
- Navigating to the copied URL includes a `/{projectId}` prefix that triggers
  a hard `window.location.replace()` reload (ProtectedRoutes.jsx) after
  stripping the prefix and validating the project.
- The modal auto-opens when the page loads with an `agentId` query param,
  no manual card click required.
- Modal content (name, description, starters, welcome message) is pre-existing
  and already covered by ELITEA-2356 (OpenAgentDetailModal test); this case
  focuses on the copy-link → navigate → auto-open flow specifically.
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


class TestAgentHubCopyLinkFromModal:
    """ELITEA-2359: Agent Hub — copy link from modal navigates to agent (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2359_copy-link-from-agent-hub-modal-navigates-to-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_copy_link_from_modal_navigates_to_agent(self, page: Page, browser):
        """Copy a link from the agent detail modal's Share action, navigate to it
        in a new page context, and verify the modal auto-opens showing the same
        agent's details (name, description, starters, welcome message)."""

        # Use an agent that has recognizable details (Entertainer Agent was used
        # in analysis, but any agent with populated fields works since the test
        # asserts non-empty content, not specific values).
        catalog_agent_name = "Entertainer Agent"

        agent_hub = AgentHubPage(page)

        with allure.step("Step 1 — Navigate to Agent Hub Catalog"):
            agent_hub.navigate()
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step(f"Step 2 — Click the '{catalog_agent_name}' agent card to open modal"):
            agent_hub.open_agent_by_name(catalog_agent_name, timeout=NAVIGATION_TIMEOUT)
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Capture modal content (name, description) before navigating"):
            modal_agent_name = (agent_hub.modal_agent_name.text_content() or "").strip()
            modal_description = (agent_hub.modal_description.text_content() or "").strip()
            assert modal_agent_name, "Modal should display agent name"
            assert modal_description, "Modal should display agent description"
            logger.info(f"Modal agent: {modal_agent_name}, description length: {len(modal_description)}")

        with allure.step("Step 4 — Click the overflow menu button"):
            agent_hub.modal_menu_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            agent_hub.modal_menu_button.click()

        with allure.step("Step 5 — Click the 'Share' menu item to copy link"):
            # Grant clipboard permissions before the action so the writeText
            # interception succeeds (the permission prompt is otherwise a hang).
            page.context.grant_permissions(["clipboard-read", "clipboard-write"])

            # Capture the clipboard.writeText() call before it fires, storing the
            # URL into a window variable (network call not fired — pure client-side
            # copy). AFS § Automation Notes: direct navigator.clipboard.readText()
            # can hang with permission denial; writeText interception is more reliable.
            page.evaluate("""
                window.copiedUrl = undefined;
                const originalWrite = navigator.clipboard.writeText;
                navigator.clipboard.writeText = function(text) {
                    window.copiedUrl = text;
                    return originalWrite.call(navigator.clipboard, text);
                };
            """)

            # Now click Share — the monkey-patch intercepts the URL.
            agent_hub.modal_share_menu_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            agent_hub.modal_share_menu_item.click()

            # Wait for the success notification (confirms the copy completed).
            agent_hub.modal_share_success_toast.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            logger.info("Share notification appeared, clipboard URL intercepted")

            # Retrieve the captured URL from the window variable.
            copied_url = page.evaluate("() => window.copiedUrl")
            assert copied_url, "Clipboard should have captured the copied URL"
            logger.info(f"Captured URL: {copied_url}")

            # Verify the URL format matches the AFS expectation:
            # http://localhost:5173/elitea-catalog?tab=agents&agentId={id}
            assert "/elitea-catalog?" in copied_url, f"URL should contain /elitea-catalog, got: {copied_url}"
            assert "agentId=" in copied_url, f"URL should contain agentId= parameter, got: {copied_url}"

        with allure.step("Step 6 — Navigate to the copied URL in a new page context"):
            # Create a new page in the same browser context (reuses auth/cookies).
            new_page = browser.new_page()
            try:
                # The URL has a /{projectId}/ prefix that triggers a hard reload
                # (ProtectedRoutes.jsx), so wait for network settle + modal render.
                new_page.goto(copied_url, wait_until="load")
                new_page.wait_for_load_state("networkidle")

                # Create a new AgentHubPage instance for the new page context.
                new_agent_hub = AgentHubPage(new_page)

                with allure.step("Step 7 — Verify the modal auto-opened with correct agent"):
                    # Modal should auto-open due to the agentId query param.
                    expect(new_agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

                    # Verify agent details match what was in the original modal.
                    reopened_agent_name = (new_agent_hub.modal_agent_name.text_content() or "").strip()
                    reopened_description = (new_agent_hub.modal_description.text_content() or "").strip()

                    assert reopened_agent_name, "Reopened modal should display agent name"
                    assert reopened_description, "Reopened modal should display agent description"
                    assert reopened_agent_name == modal_agent_name, (
                        f"Agent name should match: original='{modal_agent_name}', "
                        f"reopened='{reopened_agent_name}'"
                    )
                    assert reopened_description == modal_description, (
                        "Agent description should match the original"
                    )

                with allure.step("Step 8 — Verify CHAT STARTERS and Welcome Message sections"):
                    # These sections should be present and non-empty (or show the
                    # empty-state placeholder if no starters/welcome message exists).
                    assert new_agent_hub.modal_chat_starters_section.is_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    ), "CHAT STARTERS section should be visible"

                    assert new_agent_hub.modal_welcome_message_section.is_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    ), "Welcome Message section should be visible"

                    # Read the section text to confirm they render (no assertion
                    # on specific content since agents may have empty starters/message).
                    starters_text = new_agent_hub.modal_chat_starters_section.text_content() or ""
                    welcome_text = new_agent_hub.modal_welcome_message_section.text_content() or ""

                    assert "CHAT STARTERS" in starters_text, (
                        "CHAT STARTERS section should contain the header text"
                    )
                    assert "Welcome Message" in welcome_text, (
                        "Welcome Message section should contain the header text"
                    )

                with allure.step("Step 9 — Verify the Start Chat button is visible"):
                    assert new_agent_hub.modal_start_chat_button.is_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    ), "Start Chat button should be visible in the reopened modal"

            finally:
                new_page.close()
