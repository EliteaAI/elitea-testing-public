"""UI Test for ELITEA-3764 — Chat: Export with attachments produces a ZIP archive.

Spec: test-specs/chat-interface/l1_export-with-attachments-zip-archive_ELITEA-3764.md

Case-text drift (declared in the AFS): the context menu opens from the hover
3-dot button (not right-click); the size in the option label is formatted for
tiny files ("36 Bytes", not "X.XX MB"); the file is named
``<chat>_<date>_<time>.zip`` plus ``.enc`` on DEV because DEV serves the export
encrypted, so extracting it and inspecting the ZIP contents (case steps 11-15)
is not observable — automated as a header/size check, with a conditional ZIP
content check for environments that serve a plain archive.
"""

import logging
import re
import time
import zipfile

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
EXPORT_TOAST_TEXT = "Chat exported successfully"
ENC_HEADER = b"ELITEA-CHAT-ENC/1"
FILENAME_RE = re.compile(r"^(?P<name>.+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.zip(\.enc)?$")
OPTION_LABEL_RE = re.compile(r"With attachments \(3 files · .+\)")
HELP_TEXT = "Chat messages and all attached and generated files/images will be exported as a ZIP archive."
ATTACHMENT_NAMES = ["note_alpha.txt", "data_beta.csv", "doc_gamma.md"]


class TestChatExportWithAttachmentsZip:
    """ELITEA-3764: Export with attachments produces a ZIP archive (l1, high)."""

    @pytest.mark.tms("ELITEA-3764")
    @pytest.mark.p1
    def test_export_with_attachments_produces_zip(self, page, conversation_api, tmp_path):
        chat = ChatPage(page)
        conv_id = None
        chat_name = f"autotest_3764_{int(time.time())}"
        files = []
        for name in ATTACHMENT_NAMES:
            f = tmp_path / name
            f.write_text(f"content of {name}\n")
            files.append(str(f))
        try:
            with allure.step("Setup — create a conversation, attach 3 files and send a message"):
                conv_id = conversation_api.create_conversation(chat_name)["id"]
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                item = chat.get_conversation_item(conv_id)
                item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                item.click()
                chat.attach_files_via_menu(files)
                chat.wait_for_attachment_chip_count(3, timeout=UI_ELEMENT_TIMEOUT)
                initial = chat.get_message_count()
                chat.send_message("Reply with just OK")
                chat.wait_for_ai_response(initial_count=initial)
                chat.wait_for_generation_complete()

            with allure.step("Step 1 — Return to the chat list; the conversation is listed"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.get_conversation_item(conv_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2-3 — Open the context menu and click Export; the dialog opens"):
                chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("export", timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.export_chat_modal_chat_name).to_contain_text(chat_name)

            with allure.step("Step 4 — 'With attachments' option shows the 3-file count"):
                expect(chat.export_chat_modal_option_with).to_contain_text(OPTION_LABEL_RE, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 5 — Select 'With attachments'; the radio becomes selected"):
                radio = chat.export_chat_modal_option_radio.within(chat.export_chat_modal_option_with)
                radio.click(force=True)
                expect(radio).to_be_checked()

            with allure.step("Step 6 — Help text describes the ZIP archive export"):
                expect(chat.export_chat_modal_option_description).to_have_text(HELP_TEXT)

            with allure.step("Step 7-9 — Click Export: progress 'Exporting chat... 3 files' shows, ZIP downloads"):
                result = chat.click_export_capturing_progress()
                download = result["download"]
                assert result["progress_seen"], "Export progress block never appeared during the export"
                assert "Exporting chat... 3 files" in result["modal_text"], (
                    f"Unexpected progress text: {result['modal_text']!r}"
                )

            with allure.step("Step 10 — Download completes with a ZIP filename starting with the chat name"):
                assert download.failure() is None, f"Download failed: {download.failure()}"
                match = FILENAME_RE.match(download.suggested_filename)
                assert match, f"Unexpected export filename: {download.suggested_filename!r}"
                assert match.group("name") == chat_name, (
                    f"Filename should start with the chat name, got {download.suggested_filename!r}"
                )

            with allure.step("Step 11-15 — Saved archive is non-empty and well-formed (header / ZIP entries)"):
                saved = tmp_path / download.suggested_filename
                download.save_as(str(saved))
                data = saved.read_bytes()
                assert len(data) > 0, "Exported file is empty"
                if download.suggested_filename.endswith(".enc"):
                    assert data.startswith(ENC_HEADER), f"Unexpected encrypted-export header: {data[:40]!r}"
                else:
                    assert zipfile.is_zipfile(saved), "Exported .zip is not a valid ZIP archive"
                    with zipfile.ZipFile(saved) as zf:
                        entries = zf.namelist()
                    assert any(e.endswith(".json") for e in entries), f"No JSON in archive: {entries}"
                    for name in ATTACHMENT_NAMES:
                        assert any(e.endswith(name) for e in entries), f"{name} missing from archive: {entries}"

            with allure.step("Step 16 — Dialog closes; success notification shown, no error toast"):
                expect(chat.export_chat_modal).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.toast_message.filter(has_text=EXPORT_TOAST_TEXT).first).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.toast_message.filter(has_text="Failed to export")).to_have_count(0)
        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
