"""UI Test for ELITEA-2458 — Chat: Folder Rename — Checkmark (Confirm) Icon Validation.

Verifies ``FolderItem.jsx``'s inline rename editor confirm (checkmark) icon
enable/disable logic: the checkmark is INACTIVE whenever the folder name is
empty, 1-2 characters, or unchanged from the folder's current name, and
becomes ACTIVE only when the name is BOTH valid (3-64 chars, first-char-not-
space, allowed charset per ``ConversationNameRegExp``) AND different from the
current name. Confirms every inactive state fires no PUT request and leaves
the editor open (no-op click), and that the ACTIVE checkmark actually
persists the rename server-side.

Spec: test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md

No product defects found — all 9 case steps were executed live end-to-end
and matched ``FolderItem.jsx``'s ``isFolderNameValid``/``isFolderSaveEnabled``
logic exactly (AFS § Concrete Handles has the full source-level derivation).
Three testids were added this implementation, all landed on EliteaUI's
``automation/testids`` integration branch (commit ``0298860f``): the folder
dot-menu's "Rename" item (never had one before — zero regression history,
unlike the sibling "Delete" item, see ``ChatPage.FOLDER_MENU_DELETE_ITEM``'s
own docstring and issue #1309), a ``data-disabled`` state attribute on the
PRE-EXISTING ``chat-folder-name-confirm-button`` testid (identity unchanged,
per the testid=identity/state=data-* policy), and a tooltip-content testid
on the ``Tooltip`` wrapping that same button.

Steps 3 and 6's "click has no effect" checks assert THREE independent
signals (editor stays open + input value unchanged + no PUT fires) rather
than one, per the AFS's Axis-2 addition — a single signal could pass even if
some other unintended side effect fired. The "editor stays open" signal is
implemented as a compound check: ``folder_name_input`` stays visible with
its expected value AND ``get_folder_item(folder_id)`` resolves to ZERO
elements — ``FolderAccordion.jsx`` (which alone carries the
``chat-folder-item-{id}`` testid) only mounts when NOT editing, so a
zero-count there is the strongest available proof edit mode was never
unexpectedly exited by the no-op click.
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

ORIGINAL_FOLDER_NAME = "AutomationRenameTest"
TWO_CHAR_NAME = "AB"
THREE_CHAR_NAME = "ABC"
VALIDATION_TOOLTIP_TEXT = (
    "The folder name should be 3 to 64 characters long. It can include "
    "letters (a-z, A-Z), numbers (0-9), underscores (_), brackets ([]), "
    "parentheses (()), dots (.), hyphen(-), and spaces. Please note that "
    "the first character should not be a space."
)


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken — same idiom as the sibling folder tests' equivalent
    filter (``test_folder_creation.py``, ``test_move_conversation_to_folder.py``).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestChatFolderRenameCheckmarkValidation:
    """ELITEA-2458: Chat – Folder Rename – Checkmark (Confirm) Icon Validation (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2458_chat-folder-rename-checkmark-inactive-when-empty-less-than-3.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_folder_rename_checkmark_validation(self, page):
        """Validate the rename editor's confirm-checkmark enable/disable
        logic across empty / 2-char / unchanged / 3-char-changed states,
        and that the active checkmark actually persists the rename.

        Steps (AFS
        test-specs/chat-interface/l2_chat-folder-rename-checkmark-validation_ELITEA-2458.md):
        1. Seed a folder, open its rename editor via the dot-menu; verify
           the input is visible/focused/pre-filled with the folder's name.
        2. Clear the input entirely; verify it's empty.
        3. Verify the checkmark is inactive (data-disabled="true") and a
           click has no effect (editor stays open, no PUT, no accordion
           re-render).
        4. Type 2 characters ("AB"); verify input + still inactive.
        5. Hover the checkmark; verify the exact validation tooltip text.
        6. Restore the original (unchanged, valid) name; verify still
           inactive, NO tooltip this time, and click still has no effect.
        7. Type one more character (3 total, "ABC"); verify input.
        8. Verify the checkmark becomes active (data-disabled="false").
        9. Click the active checkmark; verify PUT -> 200, editor closes,
           folder's displayed name now reads "ABC".
        """
        chat = ChatPage(page)
        folder_id = None

        # Registered before Setup so console errors from every step are
        # captured (side-channel discipline — silent errors are the worst
        # bugs). The known, environment-wide secrets 403 noise is filtered
        # so it can't mask a genuinely new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        # Tracks every PUT to the folder-update endpoint fired during the
        # whole test — steps 3 and 6 assert NO new entry appears across an
        # inactive-checkmark click (the network-silence signal — the
        # strongest proof nothing fired server-side).
        put_requests = []

        def _on_request(request):
            if request.method == "PUT" and "/folder/prompt_lib/" in request.url:
                put_requests.append(request.url)

        page.on("request", _on_request)

        try:
            with allure.step(
                "Step 1 — Seed a folder, open its rename editor via the "
                "dot-menu; verify the input is visible, focused, and "
                "pre-filled with the folder's current name"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()

                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                    timeout=NAVIGATION_TIMEOUT,
                ) as create_response_info:
                    chat.set_folder_name(ORIGINAL_FOLDER_NAME)
                    chat.folder_name_confirm_button.click()
                create_response = create_response_info.value
                assert create_response.status == 201, (
                    "Seed folder POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                folder_id = create_response.json().get("id")
                assert folder_id is not None, (
                    "Seed folder response should include a real 'id', got: "
                    f"{create_response.json()!r}"
                )
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.get_folder_item(folder_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                logger.info("Seeded folder %s named %r", folder_id, ORIGINAL_FOLDER_NAME)

                chat.open_folder_rename_editor(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == ORIGINAL_FOLDER_NAME, (
                    "Rename editor should be pre-filled with the folder's "
                    f"current name {ORIGINAL_FOLDER_NAME!r}"
                )
                expect(chat.folder_name_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Clear the input entirely; verify it's empty"):
                chat.folder_name_input.click()
                chat.page.wait_for_timeout(100)
                chat.folder_name_input.clear()
                assert chat.folder_name_input.input_value() == "", (
                    "Input should be empty after clearing"
                )

            with allure.step(
                "Step 3 — Verify the checkmark is inactive on an empty "
                "name, and clicking it has no effect"
            ):
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="true" for an empty name'
                )

                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive checkmark"
                )
                assert chat.folder_name_input.input_value() == "", (
                    "Input should remain empty — the no-op click must not "
                    "mutate the editor's own local state either"
                )
                assert chat.get_folder_item(folder_id).count() == 0, (
                    f"Folder {folder_id} should NOT re-render as an "
                    "accordion row — that would mean edit mode exited "
                    "unexpectedly (FolderAccordion.jsx only mounts when "
                    "NOT editing)"
                )
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on an "
                    f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                'Step 4 — Type 2 characters ("AB"); verify input + still inactive'
            ):
                chat.set_folder_name(TWO_CHAR_NAME)
                assert chat.folder_name_input.input_value() == TWO_CHAR_NAME, (
                    f"Input should show {TWO_CHAR_NAME!r}"
                )
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should stay '
                    'data-disabled="true" for a 2-character name'
                )

            with allure.step(
                "Step 5 — Hover the checkmark; verify the exact validation "
                "tooltip text"
            ):
                tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=UI_ELEMENT_TIMEOUT)
                assert tooltip_text == VALIDATION_TOOLTIP_TEXT, (
                    f"Validation tooltip text mismatch — got: {tooltip_text!r}"
                )

            with allure.step(
                "Step 6 — Restore the original (unchanged, valid) name; "
                "verify still inactive, NO tooltip, and click still has no effect"
            ):
                chat.set_folder_name(ORIGINAL_FOLDER_NAME)
                assert chat.folder_name_input.input_value() == ORIGINAL_FOLDER_NAME, (
                    "Input should show the restored original name "
                    f"{ORIGINAL_FOLDER_NAME!r}"
                )
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should stay '
                    'data-disabled="true" for a valid-but-unchanged name'
                )
                tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=1500)
                assert tooltip_text == "", (
                    "No tooltip should appear for a valid (even if "
                    f"unchanged) name, got: {tooltip_text!r}"
                )

                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive "
                    "(valid-but-unchanged) checkmark"
                )
                assert chat.folder_name_input.input_value() == ORIGINAL_FOLDER_NAME, (
                    "Input should still show the unchanged original name"
                )
                assert chat.get_folder_item(folder_id).count() == 0, (
                    f"Folder {folder_id} should NOT re-render as an accordion row"
                )
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on an "
                    f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                'Step 7 — Type one more character (3 total, "ABC"); verify input'
            ):
                chat.set_folder_name(THREE_CHAR_NAME)
                assert chat.folder_name_input.input_value() == THREE_CHAR_NAME, (
                    f"Input should show {THREE_CHAR_NAME!r}"
                )

            with allure.step("Step 8 — Verify the checkmark becomes active"):
                assert chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="false" for a valid, changed name'
                )

            with allure.step(
                "Step 9 — Click the active checkmark; verify the rename "
                "persists server-side and the displayed name updates"
            ):
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as put_response_info:
                    chat.folder_name_confirm_button.click()
                put_response = put_response_info.value
                assert put_response.status == 200, (
                    f"Rename PUT should resolve 200, got {put_response.status} "
                    f"for {put_response.url}"
                )
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert THREE_CHAR_NAME in (folder_item.text_content() or ""), (
                    f"Folder {folder_id} should display the renamed name "
                    f"{THREE_CHAR_NAME!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across "
                "the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            # AFS § Cleanup CAUTION: ChatPage.delete_folder_via_menu() /
            # FOLDER_MENU_DELETE_ITEM currently target a DEAD testid
            # (regressed, tracked in
            # EliteaAI/elitea-testing-public#1309, NOT this case's own
            # scope to fix) — wrapped in try/except per the existing
            # pattern so a cleanup failure never fails the test itself.
            # A silently-failed cleanup here is expected and NOT evidence
            # this case's OWN assertions are wrong.
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2459_chat-folder-rename-validation-tooltip-for-invalid-input-and.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_folder_rename_checkmark_special_chars_and_leading_space_invalid(self, page):
        """ELITEA-2459 — two additional invalid-name scenarios beyond the
        ones test_folder_rename_checkmark_validation (ELITEA-2458) already
        covers: (a) a name containing unsupported special characters, and
        (b) a name whose FIRST character is a space (otherwise valid /
        long-enough). Both are asserted, via the SAME data-disabled /
        tooltip / no-op mechanism, to be just as inactive as the
        empty / 2-char / unchanged states ELITEA-2458 already exercises —
        proving ConversationNameRegExp's charset and first-character
        exclusions, not just its length/change gate.

        Spec: test-specs/chat-interface/lextend_folder-rename-tooltip-special-chars-and-space-first-char_ELITEA-2459.md

        No product defects found — both scenarios were executed live and
        matched FolderItem.jsx's ConversationNameRegExp logic exactly (same
        static FolderNameWarningMessage tooltip regardless of WHICH regex
        clause failed).
        """
        chat = ChatPage(page)
        folder_id = None
        seed_name = "ELITEA2459RenameTest"

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        put_requests = []

        def _on_request(request):
            if request.method == "PUT" and "/folder/prompt_lib/" in request.url:
                put_requests.append(request.url)

        page.on("request", _on_request)

        try:
            with allure.step(
                "Step 1 — Seed a folder, open its rename editor via the dot-menu"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()

                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                    timeout=NAVIGATION_TIMEOUT,
                ) as create_response_info:
                    chat.set_folder_name(seed_name)
                    chat.folder_name_confirm_button.click()
                create_response = create_response_info.value
                assert create_response.status == 201, (
                    "Seed folder POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                folder_id = create_response.json().get("id")
                assert folder_id is not None, (
                    "Seed folder response should include a real 'id', got: "
                    f"{create_response.json()!r}"
                )
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.get_folder_item(folder_id).wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                logger.info("Seeded folder %s named %r", folder_id, seed_name)

                chat.open_folder_rename_editor(folder_id, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 2 — Type unsupported special characters ("Folder$$%%"); '
                "verify invalid state, exact tooltip, and no-op click"
            ):
                chat.set_folder_name("Folder$$%%")
                assert chat.folder_name_input.input_value() == "Folder$$%%", (
                    "Input should show 'Folder$$%%' verbatim"
                )
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="true" for a name with unsupported '
                    "special characters"
                )
                tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=UI_ELEMENT_TIMEOUT)
                assert tooltip_text == VALIDATION_TOOLTIP_TEXT, (
                    f"Validation tooltip text mismatch — got: {tooltip_text!r}"
                )

                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive checkmark"
                )
                assert chat.folder_name_input.input_value() == "Folder$$%%", (
                    "Input should remain unchanged by the no-op click"
                )
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on an "
                    f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                'Step 3 — Type a leading space (" ValidRest"); verify '
                "invalid state, exact tooltip, and no-op click, despite an "
                "otherwise fully valid remainder"
            ):
                chat.set_folder_name(" ValidRest")
                assert chat.folder_name_input.input_value() == " ValidRest", (
                    "Input should show ' ValidRest' verbatim — the leading "
                    "space is accepted by the field itself"
                )
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="true" for a name starting with a '
                    "space, even though every subsequent character is "
                    "individually valid and the length is within range"
                )
                tooltip_text = chat.get_folder_name_confirm_tooltip_text(timeout=UI_ELEMENT_TIMEOUT)
                assert tooltip_text == VALIDATION_TOOLTIP_TEXT, (
                    f"Validation tooltip text mismatch — got: {tooltip_text!r}"
                )

                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive checkmark"
                )
                assert chat.folder_name_input.input_value() == " ValidRest", (
                    "Input should remain unchanged by the no-op click"
                )
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on an "
                    f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across "
                "the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename "
                    f"validation: {[m.text for m in console_messages]!r}"
                )

        finally:
            # Same caution as test_folder_rename_checkmark_validation's own
            # cleanup: delete_folder_via_menu() targets a DEAD testid
            # (regression #1309, NOT this case's scope, reconfirmed dead
            # during ELITEA-2459 exploration) — wrapped so a cleanup
            # failure never fails the test itself.
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
