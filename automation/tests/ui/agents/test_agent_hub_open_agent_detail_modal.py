"""Agent Hub — open agent detail modal (ELITEA-2356).

Verifies that clicking a Catalog agent card opens the agent preview modal as
an overlay, and that the modal displays: agent icon, agent name, owner name,
liked status (heart icon + count), the overflow menu (contains the copy-link
"Share" action), a close ("x") button, the agent's description, the CHAT
STARTERS section, the Welcome Message section, and a "Start Chat" button in
the fixed footer — with zero console errors and zero 4xx/5xx network
responses. Read-only: this test never clicks like, the overflow menu, close,
or Start Chat — see AFS § Cleanup ("None").

Spec: test-specs/agent-hub/l3_agent-hub-open-agent-detail-modal_ELITEA-2356.md

Reuses `AgentHubPage` as-is for navigation/heading/agent-card lookup and the
modal's `open_agent_by_name()` ready-signal wait (ELITEA-2075); adds 7 new
`LocatorDescriptor` fields + a `get_modal_liked_state()` helper to the same
page object for this case's modal sub-elements.

Case-text drifts (CLARIFICATION, not defects — AFS § Known Defects Found):
- "CONVERSATION STARTERS" / "Start conversation" -> live product reads "CHAT
  STARTERS" / "Start Chat" (already tracked,
  EliteaAI/elitea-testing-public#1042, names this case as an affected
  sibling). Asserted against the live copy, not the case's literal text.
- "copy link icon" -> live product has an overflow ("...") menu button whose
  "Share" item performs the copy action; there is no standalone copy-link
  icon (filed this dispatch, EliteaAI/elitea-testing-public#1218). Asserts
  the overflow menu button's visibility only — opening it is a sibling case
  (ELITEA-2359).

New testid attributes this implementation added (JSX edits, EliteaAI/EliteaUI
`automation/testids`, EliteaAI/EliteaUI@b0dc74c0):
`catalog-agent-modal-agent-icon` (EntityIcon call site), `catalog-agent-modal-
owner-name` (author Typography), `catalog-agent-modal-like-button` (threaded
`testId` prop into `<AgentHubLike>`, `data-liked` auto-derived by the shared
`Like.jsx`), `catalog-agent-modal-close-button` (close IconButton),
`catalog-agent-modal-description` (description Typography), `catalog-agent-
modal-chat-starters-section` / `catalog-agent-modal-welcome-message-section`
(new `testId` props threaded into `AgentConversationStarters`/
`AgentWelcomeMessage`, applied to each section's container `Box`).
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

CATALOG_AGENT_NAME = "User Story Creator"
EXPECTED_CHAT_STARTERS_HEADER = "CHAT STARTERS"
EXPECTED_CHAT_STARTERS_EMPTY_TEXT = "No predefined chat starters – just type your request to begin."
EXPECTED_WELCOME_MESSAGE_HEADER = "Welcome Message"
EXPECTED_WELCOME_MESSAGE_EMPTY_TEXT = "No welcome message set – the agent will start without a greeting."


class TestAgentHubOpenAgentDetailModal:
    """ELITEA-2356: Agent Hub — open agent detail modal (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2356_agent-hub-open-agent-detail-modal.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_agent_hub_open_agent_detail_modal(self, page: Page):
        """Clicking a Catalog agent card opens the preview modal as an overlay,
        displaying icon, name, owner, liked status, overflow menu, close
        button, description, CHAT STARTERS section, Welcome Message section,
        and the Start Chat button — read-only, zero console errors, zero
        4xx/5xx."""
        agent_hub = AgentHubPage(page)

        # Registered before navigation so console errors / failed network
        # responses from every step (navigate, card click, modal render) are
        # captured — AFS Expected Results require "zero console errors,
        # zero 4xx/5xx" across the whole open-modal interaction.
        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[int] = []
        page.on("response", lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None)

        with allure.step("Step 1 — Navigate to Agent Hub"):
            agent_hub.navigate()
            assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

        with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card"):
            assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
            )
            # open_agent_by_name() waits on the agent-details GET response
            # (.../public_application/prompt_lib/{id} -> 200) — the concrete,
            # deterministic ready-signal for the modal's content (AFS Axis 2 /
            # Automation Hints): a bare visibility wait risks the same race
            # class as known defect #1043.
            agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)

        with allure.step("Step 3 — Verify the agent detail modal opens as an overlay"):
            expect(agent_hub.modal_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert not console_errors, f"Unexpected console errors while opening the modal: {console_errors}"

        with allure.step(
            "Step 4 — Verify the modal displays agent icon, agent name, owner name, "
            "liked status, overflow (copy-link) menu, close button, and description"
        ):
            assert agent_hub.modal_agent_icon.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Agent icon should be visible in the preview modal"
            )
            expect(agent_hub.modal_agent_name).to_have_text(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
            owner_name = (agent_hub.modal_owner_name.text_content() or "").strip()
            assert owner_name, "Owner name should be non-empty in the preview modal"

            # Liked status: heart icon + count. This 0-like agent should show
            # data-liked="false" (Like.jsx auto-derives the state attribute
            # from the testId presence — same precedent as the card-list like
            # button, ELITEA-2354).
            assert agent_hub.get_modal_liked_state() == "false", (
                "Modal like button should show data-liked='false' for a 0-like agent"
            )

            # Case-text drift: no standalone "copy link icon" exists — the
            # live control is the overflow ("...") menu button, whose "Share"
            # item performs the copy-to-clipboard action (CLARIFICATION,
            # EliteaAI/elitea-testing-public#1218). Visibility-only — opening
            # the menu is out of scope for this case (sibling ELITEA-2359).
            assert agent_hub.modal_menu_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Overflow menu button (contains the copy-link/Share action) should be visible"
            )

            assert agent_hub.modal_close_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Close ('x') button should be visible in the preview modal header"
            )

            description = (agent_hub.modal_description.text_content() or "").strip()
            assert description, "Agent description should be non-empty in the preview modal"

        with allure.step('Step 5 — Verify the modal shows the "CHAT STARTERS" section'):
            # Case text says "CONVERSATION STARTERS" — live product reads
            # "CHAT STARTERS" (CLARIFICATION, already tracked,
            # EliteaAI/elitea-testing-public#1042, names this case as an
            # affected sibling). Asserted against the live copy.
            assert agent_hub.modal_chat_starters_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "CHAT STARTERS section should be visible in the preview modal"
            )
            starters_text = agent_hub.modal_chat_starters_section.text_content() or ""
            assert EXPECTED_CHAT_STARTERS_HEADER in starters_text, (
                f"Expected {EXPECTED_CHAT_STARTERS_HEADER!r} header text, got: {starters_text!r}"
            )
            assert EXPECTED_CHAT_STARTERS_EMPTY_TEXT in starters_text, (
                f"Expected empty-state text {EXPECTED_CHAT_STARTERS_EMPTY_TEXT!r} for a "
                f"0-starter agent, got: {starters_text!r}"
            )

        with allure.step('Step 6 — Verify the modal shows the "Welcome Message" section'):
            assert agent_hub.modal_welcome_message_section.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "Welcome Message section should be visible in the preview modal"
            )
            welcome_text = agent_hub.modal_welcome_message_section.text_content() or ""
            assert EXPECTED_WELCOME_MESSAGE_HEADER in welcome_text, (
                f"Expected {EXPECTED_WELCOME_MESSAGE_HEADER!r} header text, got: {welcome_text!r}"
            )
            assert EXPECTED_WELCOME_MESSAGE_EMPTY_TEXT in welcome_text, (
                f"Expected empty-state text {EXPECTED_WELCOME_MESSAGE_EMPTY_TEXT!r} for an "
                f"agent with no welcome message, got: {welcome_text!r}"
            )

        with allure.step(
            'Step 7 — Verify the "Start Chat" button is visible at the bottom of the modal'
        ):
            # Case text says "Start conversation" — live product reads
            # "Start Chat" (CLARIFICATION, same #1042 as step 5). This case
            # does NOT click it — starting a conversation is a materially
            # different, already-tracked sibling case (ELITEA-2360), and
            # clicking here would also risk known defect #1043 (which only
            # matters to cases that actually click it).
            assert agent_hub.modal_start_chat_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                "'Start Chat' button should be visible in the modal footer"
            )

        with allure.step("Side-channel check — zero console errors, zero 4xx/5xx"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
            assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
            console_errors.stop()
