"""UI Tests for ELITEA-2119/ELITEA-2120 — Chat: Folder Creation Inline Editor
— Custom Name Saved / Cancel Discards.

Family AFS covering two flow-variants of the same inline folder-creation
editor ELITEA-2132/ELITEA-2118 already open (``chat-create-folder-button`` ->
``chat-folder-name-input``): typing a CUSTOM name before confirming
(ELITEA-2119), and typing a name then CANCELLING (ELITEA-2120). Neither
scenario is exercised by any existing merged spec — ``test_folder_creation.py``
(ELITEA-2132) only exercises the untouched-default-name path, and
``test_chat_folder_rename_checkmark_validation.py`` (ELITEA-2458) only opens
the create-folder flow as SETUP for the RENAME editor, never asserting the
create-flow's own custom-name-save or cancel-discard behavior.

Spec: test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md

Two independent test methods, not a single ``pytest.mark.parametrize`` —
the two scenarios diverge in ACTION (confirm vs. cancel), not just data, same
precedent as the ELITEA-2110/2112/2113 family's separate "Shape A"
(parametrized) / "Shape B" (distinct action) split in
``test_conversation_rename_invalid_chars_and_recovery.py``.

No product defects were found — both cases matched ``FolderItem.jsx``'s
actual create/cancel handling exactly, live-confirmed via Playwright MCP
against ``http://localhost:5173`` before this file was written.

Extended for ELITEA-2133/ELITEA-2134 (near-total TMS-case duplicates of
ELITEA-2119/ELITEA-2120 — same flows, different literal test data):
``test_create_folder_with_custom_name`` gained a new Step 6 closing
ELITEA-2133's own gap (expand the newly-created folder, verify the empty
state — the covering test previously only verified it rendered collapsed);
``test_cancel_folder_creation_discards_folder`` gained only a second
``@allure.issue`` tag for ELITEA-2134 — zero assertion gap, every step
already covered. See
test-specs/chat-interface/lextend_chat-folder-creation-custom-name-expand-empty-state_ELITEA-2133.md
and
test-specs/chat-interface/lextend_chat-folder-creation-cancel-discard-tag-only_ELITEA-2134.md.

Further extended for ELITEA-2457 (a third near-total duplicate of the same
custom-name-and-expand flow): ``test_create_folder_with_custom_name`` gained
only a third ``@allure.issue`` tag — zero assertion gap, since ELITEA-2133's
own Step 6 already closes ELITEA-2457's expand/empty-state requirement. See
test-specs/chat-interface/lextend_chat-folder-creation-custom-name-and-expand-tag-only_ELITEA-2457.md.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CUSTOM_FOLDER_NAME = "My Sprint Folder"
CANCEL_FOLDER_NAME = "Temp Folder"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as the sibling folder tests' equivalent filter (see
    ``test_folder_creation.py``'s copy) — a ``403 Forbidden`` on
    ``GET .../secrets/secrets/default/{project_id}`` fires on every page
    load in this local environment regardless of any action taken,
    unrelated to folder creation.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestChatFolderCreationCustomNameAndCancel:
    """ELITEA-2119/ELITEA-2120: Chat – Folder Creation Inline Editor —
    Custom Name Saved / Cancel Discards (l3, medium).
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2119_chat-folder-name-edited-inline-during-creation-with-custom-name.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2133_chat-folder-creation-with-custom-name-via-chats-header-icon.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2457_chat-create-folder-with-custom-name.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_create_folder_with_custom_name(self, page):
        """Type a custom folder name during creation and confirm; verify the
        folder is saved server-side with that exact name.

        Steps (AFS
        test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md,
        ELITEA-2119 section):
        1. Navigate to chat; open the create-folder editor.
        2. Clear the default name and type 'My Sprint Folder'.
        3. Verify the checkmark icon is active.
        4. Click the checkmark; verify the POST resolves 201 with the
           expected name.
        5. Verify the input field closes and the folder shows the custom
           name as plain text.

        Step 6 (AFS
        test-specs/chat-interface/lextend_chat-folder-creation-custom-name-expand-empty-state_ELITEA-2133.md)
        closes ELITEA-2133's own case step 4 — expand the just-created
        folder and verify it shows the empty state — which was not asserted
        here before (only the collapsed render was).
        """
        chat = ChatPage(page)
        folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Navigate to chat, open the create-folder editor"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Clear the default name and type the custom name"
            ):
                chat.set_folder_name(CUSTOM_FOLDER_NAME)
                assert chat.folder_name_input.input_value() == CUSTOM_FOLDER_NAME, (
                    f"Input should read {CUSTOM_FOLDER_NAME!r} verbatim "
                    "after replacing the default name"
                )

            with allure.step("Step 3 — Verify the checkmark icon is active"):
                assert chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="false" for a valid, changed custom name'
                )

            with allure.step(
                "Step 4 — Click the checkmark icon; verify the POST "
                "resolves 201 with the custom name"
            ):
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                    timeout=NAVIGATION_TIMEOUT,
                ) as create_response_info:
                    chat.folder_name_confirm_button.click()
                create_response = create_response_info.value
                assert create_response.status == 201, (
                    f"Expected 201 from folder-create POST, got "
                    f"{create_response.status} for {create_response.url}"
                )
                body = create_response.json()
                assert body.get("name") == CUSTOM_FOLDER_NAME, (
                    f"Response body 'name' should be {CUSTOM_FOLDER_NAME!r}, "
                    f"got: {body!r}"
                )
                folder_id = body.get("id")
                assert folder_id is not None, (
                    f"Response body should include a real folder 'id', got: {body!r}"
                )

            with allure.step(
                "Step 5 — Verify the input field closes and the folder "
                "shows the custom name as plain text"
            ):
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert CUSTOM_FOLDER_NAME in (folder_item.text_content() or ""), (
                    f"Folder {folder_id} should display the name "
                    f"{CUSTOM_FOLDER_NAME!r}"
                )
                assert not chat.is_folder_expanded(folder_id), (
                    f"Newly created folder {folder_id} should render collapsed "
                    "(data-expanded=\"false\")"
                )

            with allure.step(
                "Step 6 — Click the folder to expand it; verify it shows "
                "the empty state (ELITEA-2133 case step 4 — the gap this "
                "extension closes)"
            ):
                chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_id), (
                    f"Folder {folder_id} should carry data-expanded=\"true\" "
                    "after being clicked"
                )
                empty_state_text = chat.get_folder_empty_state_text(folder_id)
                assert "No conversations added" in empty_state_text, (
                    f"Expanded empty folder {folder_id} should show the empty "
                    f"state, got: {empty_state_text!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across "
                "the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder creation: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2120_chat-folder-name-edited-inline-during-creation-cancel-discards-folder.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2134_chat-folder-creation-cancel-discards-new-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_cancel_folder_creation_discards_folder(self, page):
        """Type a name during folder creation, then click cancel (X);
        verify the creation is fully discarded — no request fires, no
        folder appears, and the folder list's total count is unchanged.

        Steps (AFS
        test-specs/chat-interface/l3_chat-folder-creation-custom-name-and-cancel_ELITEA-2119_2120.md,
        ELITEA-2120 section):
        1. Navigate to chat; open the create-folder editor.
        2. Type 'Temp Folder'.
        3. Click the X (cancel) icon.
        4. Verify no folder named 'Temp Folder' appears in the list.
        5. Verify the folder list's total count is unchanged from before the
           creation attempt, and no network request fired.

        Coverage tag chain only for ELITEA-2134 (AFS
        test-specs/chat-interface/lextend_chat-folder-creation-cancel-discard-tag-only_ELITEA-2134.md)
        — same flow, different literal discarded name ("Cancelled Folder"),
        zero assertion gap; every step is already proven above.
        """
        chat = ChatPage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        # Tracks every POST to the folder-create endpoint fired during the
        # whole test — step 5 asserts NO new entry appears across the
        # cancel click (the strongest available proof the cancel path never
        # mutates server state at all).
        post_requests = []

        def _on_request(request):
            if request.method == "POST" and "/folder/prompt_lib/" in request.url:
                post_requests.append(request.url)

        page.on("request", _on_request)

        with allure.step("Step 1 — Navigate to chat, open the create-folder editor"):
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            folder_count_before = chat.get_folder_link_count()
            chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Type the folder name to be discarded"):
            chat.set_folder_name(CANCEL_FOLDER_NAME)
            assert chat.folder_name_input.input_value() == CANCEL_FOLDER_NAME, (
                f"Input should read {CANCEL_FOLDER_NAME!r} verbatim"
            )

        with allure.step(
            "Step 3 — Click the X (cancel) icon; verify the input field "
            "closes without saving"
        ):
            chat.folder_name_cancel_button.click()
            chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Verify no folder named 'Temp Folder' appears in the list"
        ):
            matching_names = chat.get_folder_names_containing(CANCEL_FOLDER_NAME)
            assert not matching_names, (
                f"No folder should contain {CANCEL_FOLDER_NAME!r} after "
                f"cancel, found: {matching_names!r}"
            )

        with allure.step(
            "Step 5 — Verify the folder list's total count is unchanged, "
            "and no new POST request fired"
        ):
            folder_count_after = chat.get_folder_link_count()
            assert folder_count_after == folder_count_before, (
                "Folder list count should be unchanged after cancelling "
                f"creation — before={folder_count_before}, "
                f"after={folder_count_after}"
            )
            assert not post_requests, (
                "No POST to the folder-create endpoint should fire when "
                f"cancelling folder creation, saw: {post_requests!r}"
            )

        with allure.step(
            "Side-channel check — no unexpected console errors across "
            "the full flow"
        ):
            assert not console_messages, (
                "Unexpected console errors during cancelled folder "
                f"creation: {[m.text for m in console_messages]!r}"
            )
