"""UI Test for ELITEA-2195 — Chat: File Attachments, Verify Attach Files Option
Displays 10 Left Counter.

Verifies the "Attach Files" menu item inside the plus-menu popper, on a fresh
conversation with zero attachments: it shows the "10 left" counter text, has
its paperclip icon rendered, and is enabled/clickable.

Spec: test-specs/chat-interface/l3_attach-files-10-left-counter_ELITEA-2195.md

Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@a17cb22d):
- ``chat-attach-menuitem-button-icon`` — the paperclip icon (``AttachIcon``,
  first-party ``@/assets/attach-icon.svg?react`` asset) inside the popper's
  "Attach Files" menu item, computed as ``${testId}-icon`` and threaded via
  the same ``testId`` prop the menu item's own testid already uses
  (``AttachmentButton.jsx``).

New page-object surface (``ChatPage``, additive):
- ``attach_files_menuitem_icon`` ``LocatorDescriptor``.

Known defects: none for this case.

Usage:
    cd automation
    pytest tests/ui/chat/test_attach_files_10_left_counter.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000


class TestAttachFiles10LeftCounter:
    """ELITEA-2195: Chat – File Attachments – Verify Attach Files Option
    Displays 10 Left Counter (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2195_chat-file-attachments-verify-attach-files-option-displays-10-left-counter.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_attach_files_menuitem_shows_10_left_counter(self, page, conversation_id):
        """Fresh conversation, 0 attachments: 'Attach Files' shows '10 left',
        a paperclip icon, and is enabled.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)

        with allure.step("Step 1 — Navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Click the + icon, verify the popup menu opens"):
            chat.open_attach_menuitem(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.attach_files_button.is_visible(), (
                "'Attach Files' menu item should be visible once the plus menu is open"
            )

        with allure.step("Step 3 — Verify 'Attach Files' displays the '10 left' counter"):
            attach_text = chat.attach_files_button.text_content()
            assert "10 left" in attach_text, (
                f"'Attach Files' should show '10 left' on a fresh conversation with no "
                f"attachments, got {attach_text!r}"
            )

        with allure.step("Step 4 — Verify the paperclip/attachment icon is visible"):
            icon = chat.attach_files_menuitem_icon
            icon.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            assert icon.count() == 1, (
                f"'Attach Files' menu item should render exactly one paperclip icon, "
                f"got {icon.count()}"
            )

        with allure.step("Step 5 — Verify the option is clickable (enabled)"):
            assert chat.attach_files_button.is_enabled(), (
                "'Attach Files' menu item should be enabled/clickable on a fresh "
                "conversation with no attachments"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
