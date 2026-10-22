"""UI Test for ELITEA-3775 — Chat export: all messages present, in order (REDUCED observable).

Spec: test-specs/chat-interface/l1_export-json-all-messages-in-order_ELITEA-3775.md

Case-text drift (declared in the AFS): DEV serves the export AES-256-GCM encrypted
(``.json.enc``), so case steps 7-16 (open the JSON, count/first/last/middle/order/
duplicates inside the file) are not observable. They are automated as: UI message
count == API message list == the server's own export-summary count, order and
uniqueness verified on the API list, and the export download is valid and larger
than an empty chat's export. Deviation from 20 messages: 5 AI exchanges = 10 messages.
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
LIST_LOAD_TIMEOUT = 30_000
EXPORT_TOAST_TEXT = "Chat exported successfully"
ENC_HEADER = b"ELITEA-CHAT-ENC/1"
FILENAME_RE = re.compile(r"^(?P<name>.+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json(\.enc)?$")
PROMPTS = [f"Reply with just: {w}" for w in ("one", "two", "three", "four", "five")]


def _group_text(group: dict) -> str:
    items = group.get("message_items") or []
    return " ".join(
        str((i.get("item_details") or {}).get("content") or "") for i in items if i.get("item_type") == "text_message"
    )


def _norm(text: str) -> str:
    return " ".join(text.split())


def _export(chat: ChatPage, conv_id, tmp_path):
    chat.open_conversation_context_menu(conv_id, timeout=UI_ELEMENT_TIMEOUT)
    chat.click_conversation_menu_item("export", timeout=UI_ELEMENT_TIMEOUT)
    expect(chat.export_chat_modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
    download = chat.click_export_and_capture_download()
    expect(chat.export_chat_modal).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
    assert download.failure() is None, f"Download failed: {download.failure()}"
    saved = tmp_path / f"{conv_id}_{download.suggested_filename}"
    download.save_as(str(saved))
    return download, saved.read_bytes()


class TestChatExportJsonMessageOrder:
    """ELITEA-3775: exported chat holds all messages in chronological order (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-3775_json-all-messages-correct-order.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.tms("ELITEA-3775")
    @pytest.mark.p0
    def test_export_contains_all_messages_in_order(self, page, conversation_api, tmp_path):
        chat = ChatPage(page)
        conv_ids = []
        stamp = int(time.time())
        empty_name = f"autotest_3775_empty_{stamp}"
        chat_name = f"autotest_3775_{stamp}"
        try:
            with allure.step("Step 1 — Setup: create an empty chat and a chat to seed; open the chat list"):
                empty_id = conversation_api.create_conversation(empty_name)["id"]
                conv_ids.append(empty_id)
                conv_id = conversation_api.create_conversation(chat_name)["id"]
                conv_ids.append(conv_id)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.dismiss_platform_banner_dialog()
                # Sidebar list is fetched async after load; budget for gate-load latency.
                chat.get_conversation_item(conv_id).wait_for(state="visible", timeout=LIST_LOAD_TIMEOUT)
                chat.click_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Seed the chat with five AI exchanges (10 messages)"):
                for prompt in PROMPTS:
                    count_before = chat.get_message_count()
                    chat.send_message(prompt, use_enter=True)
                    chat.wait_for_ai_response(initial_count=count_before)

            with allure.step("Step 3 — Record UI message count, first and last message"):
                ui_count = chat.get_message_count()
                assert ui_count == 2 * len(PROMPTS), f"Expected {2 * len(PROMPTS)} messages in UI, got {ui_count}"
                ui_first = chat.get_message_text_at(0)
                ui_last = chat.get_last_message_text()
                assert PROMPTS[0] in ui_first, f"First UI message should be the first prompt, got {ui_first!r}"
                assert ui_last.strip(), "Last UI message is empty"

            with allure.step("Step 4 — API message list: count matches UI, ascending order, unique ids, first/last match"):
                groups = conversation_api.get_message_groups(conv_id)
                assert len(groups) == ui_count, f"API has {len(groups)} messages, UI shows {ui_count}"
                stamps = [g["created_at"] for g in groups]
                assert stamps == sorted(stamps), f"Messages not in ascending created_at order: {stamps}"
                ids = [g["id"] for g in groups]
                assert len(set(ids)) == len(ids), f"Duplicate message ids: {ids}"
                assert PROMPTS[0] in _group_text(groups[0]), f"First API message mismatch: {_group_text(groups[0])!r}"
                for i, prompt in enumerate(PROMPTS):
                    assert prompt in _group_text(groups[2 * i]), (
                        f"User message {i} out of order: {_group_text(groups[2 * i])!r}"
                    )
                api_last, ui_last_n = _norm(_group_text(groups[-1])), _norm(ui_last)
                assert api_last, "Last API message is empty"
                assert ui_last_n in api_last or api_last in ui_last_n, (
                    f"Last message differs: UI {ui_last_n!r} vs API {api_last!r}"
                )

            with allure.step("Step 5 — Server export summary counts exactly the conversation's messages"):
                summary = conversation_api.get_export_summary(conv_id)
                assert summary["messages_count"] == ui_count, (
                    f"Export summary messages_count {summary['messages_count']} != UI count {ui_count}"
                )

            with allure.step("Step 6 — Baseline: export the EMPTY chat"):
                _, empty_data = _export(chat, empty_id, tmp_path)
                assert len(empty_data) > 0, "Empty-chat export is empty"

            with allure.step("Step 7 — Export the seeded chat: download valid, toast shown, larger than empty export"):
                download, data = _export(chat, conv_id, tmp_path)
                expect(chat.toast_message.filter(has_text=EXPORT_TOAST_TEXT).first).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                match = FILENAME_RE.match(download.suggested_filename)
                assert match, f"Unexpected export filename: {download.suggested_filename!r}"
                assert match.group("name") == chat_name
                if download.suggested_filename.endswith(".enc"):
                    assert data.startswith(ENC_HEADER), f"Unexpected encrypted-export header: {data[:40]!r}"
                else:
                    payload = json.loads(data)
                    assert len(payload["messages"]) == ui_count
                # Weak proxy: content is encrypted on DEV, so size growth is the only file-level signal.
                assert len(data) > len(empty_data), (
                    f"Chat with messages ({len(data)} B) should export larger than empty chat ({len(empty_data)} B)"
                )
        finally:
            for cid in conv_ids:
                try:
                    conversation_api.delete_conversation(cid)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", cid, exc)
