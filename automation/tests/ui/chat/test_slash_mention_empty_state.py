"""UI Test for ELITEA-2202 — Chat: Slash Commands, Typing '/' With No
Toolkits/MCPs Shows Empty Dropdown.

Verifies that typing '/' in the message input, with zero toolkit/MCP
participants on the conversation, opens a dropdown titled "Mention Toolkit
or MCP" whose body reads exactly "No matching results" (no items), and that
clicking outside the dropdown closes it.

Spec: test-specs/chat-interface/l3_slash-mention-empty-state_ELITEA-2202.md

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@34319b30):
- ``slash-mention-list`` — the slash-mention dropdown's outer container
  (``NewParticipantList.jsx``), threaded through a new, opt-in
  ``containerTestId`` prop (default ``undefined`` — ``RecommendationList``/
  ``SearchResultList``, the component's other callers, are unaffected).
  Wired at ``SlashSuggestionList.jsx``'s toolkit-phase call site only.
- ``slash-mention-item-{project_id}_{toolkit_id}`` (dynamic) — per-item
  card in the dropdown (``NewParticipantCard.jsx``), same opt-in-prop
  mechanism (``getItemTestId``). Not exercised by this empty-state case
  (there are no items), but the ``SLASH_MENTION_ITEM_PREFIX`` absence check
  below depends on it existing.

New page-object surface (``ChatPage``, all additive):
- ``slash_mention_list`` (LocatorDescriptor)
- ``open_slash_mention_dropdown()`` / ``close_slash_mention_dropdown()``
- ``SLASH_MENTION_ITEM_PREFIX`` (class constant, for the zero-items check)

Known defects: none for this case (see AFS § Known Defects Found).

Usage:
    cd automation
    pytest tests/ui/chat/test_slash_mention_empty_state.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

EXPECTED_TITLE = "Mention Toolkit or MCP"
EXPECTED_EMPTY_BODY = "No matching results"


class TestSlashMentionEmptyState:
    """ELITEA-2202: Chat – Slash Commands – Typing '/' With No Toolkits/MCPs
    Shows Empty Dropdown (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2202_chat-slash-commands-verify-typing-when-no-toolkits-or-mcps-are-added-displays-empty-results.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_slash_mention_empty_dropdown_with_no_participants(self, page, conversation_id):
        """Typing '/' with zero toolkit/MCP participants shows an empty
        'Mention Toolkit or MCP' dropdown, which closes on an outside click.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)

        with allure.step(
            "Step 1 — Navigate to a conversation with no toolkit/MCP "
            "participants; verify PARTICIPANTS has no TOOLKITS or MCPS"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            assert not chat.is_participants_badge_visible(section="toolkits"), (
                "Fresh conversation should have no TOOLKITS participants badge"
            )
            assert not chat.is_participants_badge_visible(section="mcp"), (
                "Fresh conversation should have no MCP participants badge"
            )

        with allure.step("Step 2 — Click the message input, type '/', verify the dropdown heading"):
            chat.open_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            dropdown_text = chat.slash_mention_list.text_content() or ""
            assert EXPECTED_TITLE in dropdown_text, (
                f"Expected dropdown to contain heading {EXPECTED_TITLE!r}, got: {dropdown_text!r}"
            )

        with allure.step("Step 3 — Verify the dropdown body reads 'No matching results' with zero items"):
            assert EXPECTED_EMPTY_BODY in dropdown_text, (
                f"Expected dropdown to contain {EXPECTED_EMPTY_BODY!r}, got: {dropdown_text!r}"
            )
            item_count = chat.get_slash_mention_item_count()
            assert item_count == 0, f"Expected zero toolkit/MCP items in the dropdown, found {item_count}"

        with allure.step("Step 4 — Click outside the dropdown; verify it closes"):
            chat.close_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.slash_mention_list.count() == 0, "Dropdown should be detached after an outside click"

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
