"""UI Test for ELITEA-3784 — Chat: Export button triggers download (JSON path).

Spec: test-specs/chat-interface/l1_export-button-triggers-download_ELITEA-3784.md

Case-text drift (declared in the AFS): the context menu opens from the hover
3-dot button (not right-click), and DEV serves the export encrypted
(``.json.enc``), so "open the file" is automated as a header/size check.
The ZIP / progress branch (case step 8) needs an attachment-bearing chat and
is not covered here.
"""

import json
import logging
import re
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
EXPORT_TOAST_TEXT = "Chat exported successfully"
ENC_HEADER = b"ELITEA-CHAT-ENC/1"
FILENAME_RE = re.compile(r"^(?P<name>.+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json(\.enc)?$")


def _export_and_read(chat: ChatPage, conv_id, tmp_path):
    """Open the Export dialog for ``conv_id``, export without attachments, return (download, bytes)."""
    chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
    chat.click_conversation_menu_item("export", timeout=UI_ELEMENT_TIMEOUT)
    expect(chat.export_chat_modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
    download = chat.click_export_and_capture_download()
    expect(chat.export_chat_modal).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
    assert download.failure() is None, f"Download failed: {download.failure()}"
    saved = tmp_path / f"{conv_id}_{download.suggested_filename}"
    download.save_as(str(saved))
    return download, saved.read_bytes()


class TestChatExportDownload:
    """ELITEA-3784: Export button triggers a download (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-3784_export-button-triggers-download.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-3784")
    @pytest.mark.p0
    def test_export_button_triggers_download(self, page, conversation_api, tmp_path):
        chat = ChatPage(page)
        conv_id = None
        chat_name = f"autotest_3784_{int(time.time())}"
        try:
            with allure.step("Setup — create a conversation via API and open the chat list"):
                conv_id = conversation_api.create_conversation(chat_name)["id"]
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                chat.get_conversation_item(conv_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 1-2 — Open the conversation's context menu; Export item is present"):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_menu_item("export")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Click Export: the Export chat dialog opens for this chat"):
                chat.click_conversation_menu_item("export", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal_chat_name).to_contain_text(chat_name)

            with allure.step("Step 4 — Export button is visible and enabled"):
                expect(chat.export_chat_modal_export_button).to_be_visible()
                expect(chat.export_chat_modal_export_button).to_be_enabled()
                expect(chat.export_chat_modal_export_button).to_have_text("Export")

            with allure.step("Step 5 — Export option selected (default 'Without attachments'; 'With' disabled, no attachments)"):
                expect(chat.export_chat_modal_option_radio.within(chat.export_chat_modal_option_without)).to_be_checked()
                expect(chat.export_chat_modal_option_radio.within(chat.export_chat_modal_option_with)).to_be_disabled()
                expect(chat.export_chat_modal_option_description).to_contain_text(
                    "Only chat messages will be exported as a JSON file."
                )

            with allure.step("Step 6-7 — Click Export: a download is initiated immediately"):
                download = chat.click_export_and_capture_download()

            with allure.step("Step 9 — Dialog closes after the export is initiated"):
                expect(chat.export_chat_modal).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 10 — Success notification 'Chat exported successfully', no error toast"):
                expect(chat.toast_message.filter(has_text=EXPORT_TOAST_TEXT).first).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.toast_message.filter(has_text="Failed to export")).to_have_count(0)

            with allure.step("Step 11-15 — Download completes, file saved, non-empty and well-formed"):
                assert download.failure() is None, f"Download failed: {download.failure()}"
                match = FILENAME_RE.match(download.suggested_filename)
                assert match, f"Unexpected export filename: {download.suggested_filename!r}"
                assert match.group("name") == chat_name, (
                    f"Filename should start with the chat name, got {download.suggested_filename!r}"
                )
                saved = tmp_path / download.suggested_filename
                download.save_as(str(saved))
                data = saved.read_bytes()
                assert len(data) > 0, "Exported file is empty"
                if download.suggested_filename.endswith(".enc"):
                    assert data.startswith(ENC_HEADER), f"Unexpected encrypted-export header: {data[:40]!r}"
                else:
                    json.loads(data)
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-3762_export-conversation-without-attachments-json-download.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-3762")
    @pytest.mark.p1
    def test_export_chat_with_messages_without_attachments(self, page, conversation_api, tmp_path):
        """ELITEA-3762: a chat with text messages and no attachments exports as a download (JSON path)."""
        chat = ChatPage(page)
        conv_ids = []
        stamp = int(time.time())
        empty_name = f"autotest_3762_empty_{stamp}"
        chat_name = f"autotest_3762_{stamp}"
        try:
            with allure.step("Step 1 — Setup: create an empty chat and a chat to seed; open the list"):
                empty_id = conversation_api.create_conversation(empty_name)["id"]
                conv_ids.append(empty_id)
                conv_id = conversation_api.create_conversation(chat_name)["id"]
                conv_ids.append(conv_id)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                chat.get_conversation_item(conv_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Seed the chat with two text exchanges (no attachments)"):
                chat.click_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                for prompt in ("Reply with just: one", "Reply with just: two"):
                    count_before_send = chat.get_message_count()
                    chat.send_message(prompt)
                    chat.wait_for_ai_response(initial_count=count_before_send)

            with allure.step("Step 3 — Baseline: export the EMPTY chat and capture its file size"):
                _, empty_data = _export_and_read(chat, empty_id, tmp_path)
                assert len(empty_data) > 0, "Empty-chat export is empty"

            with allure.step("Step 4-7 — Export dialog: chat name, default option, help text"):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_menu_item("export")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("export", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal_chat_name).to_contain_text(chat_name)
                expect(chat.export_chat_modal_option_radio.within(chat.export_chat_modal_option_without)).to_be_checked()
                expect(chat.export_chat_modal_option_radio.within(chat.export_chat_modal_option_with)).to_be_disabled()
                expect(chat.export_chat_modal_option_description).to_contain_text(
                    "Only chat messages will be exported as a JSON file."
                )
                expect(chat.export_chat_modal_export_button).to_be_enabled()

            with allure.step("Step 8 — Click Export: a download is initiated"):
                download = chat.click_export_and_capture_download()

            with allure.step("Step 15 — Dialog closes; success toast shown, no error toast"):
                expect(chat.export_chat_modal).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.toast_message.filter(has_text=EXPORT_TOAST_TEXT).first).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.toast_message.filter(has_text="Failed to export")).to_have_count(0)

            with allure.step("Step 9-14 — File name, header, messages included (size > empty export)"):
                assert download.failure() is None, f"Download failed: {download.failure()}"
                match = FILENAME_RE.match(download.suggested_filename)
                assert match, f"Unexpected export filename: {download.suggested_filename!r}"
                assert match.group("name") == chat_name, (
                    f"Filename should start with the chat name, got {download.suggested_filename!r}"
                )
                saved = tmp_path / download.suggested_filename
                download.save_as(str(saved))
                data = saved.read_bytes()
                if download.suggested_filename.endswith(".enc"):
                    assert data.startswith(ENC_HEADER), f"Unexpected encrypted-export header: {data[:40]!r}"
                else:
                    json.loads(data)
                # Weak proxy: DEV encrypts the export (AES-256-GCM), so message content, order and
                # ISO 8601 timestamps (case steps 10-14) cannot be inspected; size growth is the
                # only observable that the messages were included.
                assert len(data) > len(empty_data), (
                    f"Chat with messages ({len(data)} B) should export larger than empty chat ({len(empty_data)} B)"
                )
        finally:
            for cid in conv_ids:
                try:
                    conversation_api.delete_conversation(cid)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", cid, exc)
