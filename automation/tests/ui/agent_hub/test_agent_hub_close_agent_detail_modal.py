"""Agent Hub — close agent detail modal with X button (ELITEA-2357).

Verifies that clicking the X (close) button in the agent preview modal closes
the modal overlay, with zero console errors and zero 4xx/5xx network responses.
The user remains on the Agent Hub / Catalog list view after the modal closes.
Read-only: this test never starts chat, likes, or interacts with the overflow
menu — only opens and closes the modal.

Spec: test-specs/agent-hub/l3_agent-hub-close-agent-detail-modal-with-x-button_ELITEA-2357.md

Prerequisite: ELITEA-2356 (open agent detail modal) — reuses the same
navigate/open flow and adds the close_modal() method to AgentHubPage.
No new testids required — both modal and close button testids were added in
ELITEA-2356 work (on automation/testids, awaiting human cherry-pick to main).
"""

import logging

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from playwright.sync_api import Page, expect

logger = logging.getLogger("elitea.tests.agents")

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.regression, pytest.mark.p2, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CATALOG_AGENT_NAME = "User Story Creator"


class TestAgentHubCloseAgentDetailModal:
    """ELITEA-2357: Agent Hub — close agent detail modal with X button (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2357_agent-hub-close-agent-detail-modal-with-x-button.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_close_agent_detail_modal(self, page: Page):
        """Clicking the X button in the agent detail modal closes the modal,
        and the user remains on the Catalog list view — read-only, zero
        console errors, zero 4xx/5xx."""
        agent_hub = AgentHubPage(page)

        # Registered before navigation so console errors / failed network
        # responses from every step (navigate, open, close) are captured —
        # AFS Expected Results require "zero console errors, zero 4xx/5xx"
        # across the whole open-and-close interaction.
        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[int] = []
        page.on("response", lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None)

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card to open the detail modal"):
            assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
            )
            agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 3 — Verify the agent detail modal is displayed as an overlay"):
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

        with allure.step("Step 4 — Click the X button in the top-right corner of the modal"):
            assert agent_hub.modal_close_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Close ('x') button should be visible in the preview modal header"
            )
            agent_hub.close_modal(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Verify the modal closes"):
            # After close_modal() returns, the modal should already be in
            # hidden state (the method waits for it). Verify by double-checking.
            expect(agent_hub.modal_dialog).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert not console_errors, f"Unexpected console errors during modal close: {console_errors}"

        with allure.step("Step 6 — Verify the user remains on the Agent Hub list view"):
            # URL should still be /elitea-catalog
            assert page.url.endswith("/elitea-catalog"), (
                f"Page URL should remain /elitea-catalog after modal close, got: {page.url}"
            )
            # Catalog page heading should still be visible
            assert agent_hub.page_heading.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Catalog page heading should remain visible after modal close"
            )
            # Agent cards should still be rendered
            initial_card_count = agent_hub.get_agent_card_count()
            assert initial_card_count > 0, "Agent cards should remain visible in the Catalog after modal close"

        with allure.step("Side-channel check — zero console errors, zero 4xx/5xx"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
            assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
            console_errors.stop()
