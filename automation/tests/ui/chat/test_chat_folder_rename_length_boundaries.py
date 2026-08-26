"""UI Test for ELITEA-2128/ELITEA-2129 — Chat: Folder Rename — Length Boundary
and Cannot Type/Paste Beyond 50 Characters.

Mirrors ``test_conversation_rename_length_boundaries.py`` (ELITEA-2101/2102/
2103/2104), applied to the FOLDER entity instead of the conversation entity —
``FolderItem.jsx``'s ``onChangeFolderName`` uses the SAME
``MAX_CONVERSATION_LENGTH = 50`` slice-truncation mechanism as
``ConversationItem.jsx``'s ``onChangeConversationName``, source-confirmed AND
live-confirmed independently this session (AFS § Automation Hints has the
exact source pointers).

ELITEA-2128 — Chat: Folder Rename — Maximum 50 Characters Accepted. Typing
exactly 50 characters lands ALL 50 (no truncation — 50 is the boundary where
truncation would first bite the 51st character, not the 50th itself); the
checkmark then saves successfully.

Spec: test-specs/chat-interface/l3_chat-folder-rename-max-50-chars-accepted_ELITEA-2128.md

ELITEA-2129 — Chat: Folder Rename — Cannot Type or Paste Beyond 50 Characters.
A single flow (per the case's own step sequence) exercises BOTH overflow
techniques: typing 51 characters truncates to 50, then (after clearing the
input — isolates the paste technique from the typed value, same pattern
ELITEA-2104 uses for the conversation-entity sibling) pasting a 70-character
clipboard string (real ``navigator.clipboard.writeText()`` + a genuine
``Control+V``/``Meta+V`` keypress, NOT DOM injection) also truncates to 50 —
both reach the SAME ``onChangeFolderName`` code path, since no separate
``onPaste`` handler exists on the input (source-confirmed). The checkmark
then saves the resulting 50-character name successfully.

Spec: test-specs/chat-interface/l3_chat-folder-rename-cannot-type-or-paste-beyond-50-chars_ELITEA-2129.md

No product defects found — both cases pass end-to-end against the live
product exactly as their own case text (title, Test Data, Pass/Fail criteria)
expects. ELITEA-2129's own step 2 Expected Result column ("Only first 64
characters accepted; 65th is not entered") contradicts the rest of that same
case (title, Test Data, steps 3-4, all correctly say 50) — live execution
confirms 50 is the real, internally-consistent boundary. This test asserts
the live, self-consistent 50-character behavior throughout, per the
reverse-masking guard (case-text drift documented in the AFS § Known Defects
Found and in ``test-specs/chat-interface/_surface.md``, NOT asserted here as
"64"/"65th").
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken — same idiom as every sibling chat rename test.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _seed_folder(chat: ChatPage, name: str) -> int:
    """Create a folder via the UI's own "Create folder" flow and return its id.

    No folder-creation API client exists on this project (only
    ``delete_folder_via_api()`` does) — matches the existing
    ``test_chat_folder_rename_checkmark_validation.py`` precedent of seeding
    via the UI's create-folder editor + the POST response's ``id``.
    """
    chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
    with chat.page.expect_response(
        lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
        timeout=NAVIGATION_TIMEOUT,
    ) as create_response_info:
        chat.set_folder_name(name)
        chat.folder_name_confirm_button.click()
    create_response = create_response_info.value
    assert create_response.status == 201, (
        f"Seed folder POST should resolve 201, got {create_response.status} "
        f"for {create_response.url}"
    )
    folder_id = create_response.json().get("id")
    assert folder_id is not None, (
        f"Seed folder response should include a real 'id', got: {create_response.json()!r}"
    )
    chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
    chat.get_folder_item(folder_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
    logger.info("Seeded folder %s named %r", folder_id, name)
    return folder_id


class TestChatFolderRenameLengthBoundaries:
    """ELITEA-2128: Chat – Folder Rename – Maximum 50 Characters Accepted (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2128_chat-folder-rename-maximum-50-characters-accepted.md",
        "onetest-ai Test Case link — ELITEA-2128",
    )
    @pytest.mark.p2
    def test_rename_folder_length_boundary_50_chars_accepted(self, page):
        """Rename a folder to an exactly-50-character name; verify no truncation.

        Steps (AFS
        test-specs/chat-interface/l3_chat-folder-rename-max-50-chars-accepted_ELITEA-2128.md):
        1. Seed a folder, open its rename editor via the dot-menu -> inline
           input editable.
        2. Clear + type exactly 50 characters -> input value length == 50
           (no truncation); checkmark data-disabled == "false".
        3. Explicit click on the checkmark -> input closes, folder row
           shows the new 50-character name, PUT .../folder/... resolves
           200, no error toast, no new console errors.
        """
        case_id = "ELITEA-2128"
        new_name = "A" * 50
        chat = ChatPage(page)
        folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — seed folder_target via UI; navigate to chat"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                folder_id = _seed_folder(chat, "at_folder_len50_orig")

            with allure.step(
                f"[{case_id}] Step 1 — Open folder_target's rename editor via "
                "the dot-menu; verify the input is visible and pre-filled"
            ):
                chat.open_folder_rename_editor(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.folder_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == "at_folder_len50_orig", (
                    "Rename editor should be pre-filled with the folder's current name"
                )

            with allure.step(
                f"[{case_id}] Step 2 — Clear the input and type exactly 50 "
                "characters; verify the input value's length == 50 (no "
                'truncation) and the checkmark flips to data-disabled="false"'
            ):
                chat.set_folder_name(new_name)
                input_value = chat.folder_name_input.input_value()
                assert len(input_value) == 50, (
                    f"[{case_id}] Input value should hold exactly 50 "
                    f"characters (no truncation), got {len(input_value)}: "
                    f"{input_value!r}"
                )
                assert input_value == new_name, (
                    f"[{case_id}] Input value should be exactly {new_name!r}, "
                    f"got {input_value!r}"
                )
                assert chat.is_folder_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the name changed and '
                    "passes ConversationNameRegExp"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Explicit click on the checkmark "
                "(save) icon; verify the input closes, the folder row "
                "shows the new 50-character name, and the underlying PUT "
                "resolves 200"
            ):
                rename_put_requests = chat.capture_requests_matching("/folder/prompt_lib", method="PUT")
                chat.folder_name_confirm_button.click()

                expect(chat.folder_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_folder_item(folder_id)).to_contain_text(
                    new_name, timeout=UI_ELEMENT_TIMEOUT
                )

                assert rename_put_requests, (
                    f"[{case_id}] A PUT to /folder/prompt_lib/... should "
                    "have fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    f"[{case_id}] The rename PUT request should resolve "
                    f"200, got: {rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

                error_toast = chat.get_toast_alert("error")
                assert error_toast.count() == 0, (
                    f"[{case_id}] No error toast should be shown after a "
                    f"successful rename, found: {error_toast.count()}"
                )
                assert not console_messages, (
                    f"[{case_id}] Unexpected console errors during the "
                    f"rename flow: {[m.text for m in console_messages]!r}"
                )

        finally:
            page.remove_listener("console", _on_console)
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id)
                    logger.info("[%s] Cleaned up folder_target %s", case_id, folder_id)
                except Exception as exc:
                    logger.warning(
                        "[%s] Failed to delete folder_target %s: %s", case_id, folder_id, exc
                    )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2129_chat-folder-rename-cannot-type-or-paste-beyond-50-characters.md",
        "onetest-ai Test Case link — ELITEA-2129",
    )
    @pytest.mark.p2
    def test_rename_folder_type_and_paste_beyond_max_length_truncates(self, page):
        """ELITEA-2129: Chat – Folder Rename – Cannot Type or Paste Beyond 50 Characters.

        A single flow (per the case's own step sequence) exercises both
        overflow techniques on the SAME rename editor: typing 51 characters
        truncates to 50 (the 51st keystroke silently dropped by the
        product's own client-side ``slice(0, 50)``), then pasting a
        70-character clipboard string over that value ALSO truncates to 50
        (reached via the same ``onChange`` code path, no separate
        ``onPaste`` handler exists). The checkmark then saves the resulting
        50-character name successfully.

        Spec: test-specs/chat-interface/l3_chat-folder-rename-cannot-type-or-paste-beyond-50-chars_ELITEA-2129.md

        Steps (AFS):
        1. Seed a folder, open its rename editor via the dot-menu -> inline
           input editable.
        2. Clear + type 51 characters via per-keystroke simulation
           (``press_sequentially``, NOT ``fill()``) -> input value length
           == 50 (51st char dropped); value == "B"*50; checkmark
           data-disabled == "false". (Case-text drift: the case's own step
           2 Expected Result says "64"/"65th" — contradicts the rest of the
           same case; 50 is the live, internally-consistent boundary, see
           AFS § Known Defects Found.)
        3. Clear the input, then paste a 70-character clipboard string via a
           REAL ``navigator.clipboard.writeText()`` + ``Control+V``/
           ``Meta+V`` keypress (NOT DOM injection) -> input value length
           <= 50 (chars 51-70 dropped); value == first 50 chars of the
           pasted string.
        4. Explicit click on the checkmark -> input closes, folder row
           shows the new 50-character name, PUT .../folder/... resolves
           200, no error toast, no new console errors.
        """
        case_id = "ELITEA-2129"
        type_name = "B" * 51
        expected_typed_name = "B" * 50
        paste_source = "C" * 70
        expected_pasted_name = "C" * 50
        chat = ChatPage(page)
        folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"[{case_id}] Setup — seed folder_target via UI; navigate to chat"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                folder_id = _seed_folder(chat, "at_folder_overflow_orig")

            with allure.step(
                f"[{case_id}] Step 1 — Open folder_target's rename editor via "
                "the dot-menu; verify the input is visible and pre-filled"
            ):
                chat.open_folder_rename_editor(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.folder_name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"[{case_id}] Step 2 — Clear the input and attempt to TYPE 51 "
                "characters via per-keystroke simulation; verify only the "
                "first 50 land (51st silently dropped) and the checkmark's "
                'data-disabled flips to "false"'
            ):
                chat.set_folder_name(type_name)
                input_value = chat.folder_name_input.input_value()
                assert len(input_value) == 50, (
                    f"[{case_id}] Input value should hold exactly 50 "
                    f"characters (51st dropped), got {len(input_value)}: "
                    f"{input_value!r}"
                )
                assert input_value == expected_typed_name, (
                    f"[{case_id}] Input value should be exactly "
                    f"{expected_typed_name!r} (left-slice truncation), got "
                    f"{input_value!r}"
                )
                assert chat.is_folder_name_confirm_enabled(), (
                    f"[{case_id}] Checkmark should flip to "
                    'data-disabled="false" once the truncated 50-char '
                    "value passes ConversationNameRegExp"
                )

            with allure.step(
                f"[{case_id}] Step 3 — Clear the input (isolates the paste "
                "technique from step 2's typed value, same pattern "
                "ELITEA-2104 uses for the conversation-entity sibling), then "
                "paste a 70-character clipboard string via a REAL clipboard "
                "write + Control+V/Meta+V; verify only the first 50 "
                "characters land"
            ):
                chat.clear_folder_name()
                expect(chat.folder_name_input).to_have_value("", timeout=UI_ELEMENT_TIMEOUT)
                chat.paste_folder_name(paste_source)
                expect(chat.folder_name_input).to_have_value(
                    expected_pasted_name, timeout=UI_ELEMENT_TIMEOUT
                )
                input_value = chat.folder_name_input.input_value()
                assert len(input_value) <= 50, (
                    f"[{case_id}] Input value must never exceed 50 "
                    f"characters after paste, got {len(input_value)}: "
                    f"{input_value!r}"
                )
                assert input_value == expected_pasted_name, (
                    f"[{case_id}] Input value should be exactly "
                    f"{expected_pasted_name!r} (left-slice truncation, no "
                    "reordered/dropped-from-the-middle corruption), got "
                    f"{input_value!r}"
                )

            with allure.step(
                f"[{case_id}] Step 4 — Explicit click on the checkmark (save) "
                "icon; verify the input closes, the folder row shows the new "
                "50-character name, the underlying PUT resolves 200, no "
                "error toast, no new console errors"
            ):
                rename_put_requests = chat.capture_requests_matching("/folder/prompt_lib", method="PUT")
                chat.folder_name_confirm_button.click()

                expect(chat.folder_name_input).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_folder_item(folder_id)).to_contain_text(
                    expected_pasted_name, timeout=UI_ELEMENT_TIMEOUT
                )

                assert rename_put_requests, (
                    f"[{case_id}] A PUT to /folder/prompt_lib/... should "
                    "have fired when the checkmark was clicked"
                )
                assert rename_put_requests[-1]["status"] == 200, (
                    f"[{case_id}] The rename PUT request should resolve "
                    f"200, got: {rename_put_requests[-1]}"
                )
                rename_put_requests.stop()

                error_toast = chat.get_toast_alert("error")
                assert error_toast.count() == 0, (
                    f"[{case_id}] No error toast should be shown after a "
                    f"successful rename, found: {error_toast.count()}"
                )
                assert not console_messages, (
                    f"[{case_id}] Unexpected console errors during the "
                    f"rename flow: {[m.text for m in console_messages]!r}"
                )

        finally:
            page.remove_listener("console", _on_console)
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id)
                    logger.info("[%s] Cleaned up folder_target %s", case_id, folder_id)
                except Exception as exc:
                    logger.warning(
                        "[%s] Failed to delete folder_target %s: %s", case_id, folder_id, exc
                    )
