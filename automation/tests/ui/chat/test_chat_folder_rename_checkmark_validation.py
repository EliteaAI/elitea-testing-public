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

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

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
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2125_chat-folder-rename-check-icon-inactive-for-less-than-3-characters.md",
        "onetest-ai Test Case link — ELITEA-2125",
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
                "Step 4a — ELITEA-2125: click the checkmark while the name "
                'is 2 characters ("AB"); verify it has no effect'
            ):
                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive "
                    "(2-character) checkmark"
                )
                assert chat.folder_name_input.input_value() == TWO_CHAR_NAME, (
                    "Input should remain unchanged by the no-op click"
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
            # AFS § Cleanup CAUTION: FOLDER_MENU_DELETE_ITEM (the dot-menu
            # "Delete" item) is a DEAD testid on EliteaUI (regressed,
            # tracked in EliteaAI/elitea-testing-public#1309, NOT this
            # case's own scope to fix). delete_folder_via_menu() now falls
            # back to a direct API delete when that testid doesn't appear
            # (see its own docstring), so cleanup succeeds via that path
            # while #1309 stays open — this try/except remains only as a
            # last-resort net for a genuinely unreachable API (e.g. a dead
            # backend), not because cleanup is expected to silently no-op.
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

        Both no-op-click checks use the SAME THREE-independent-signal
        pattern test_folder_rename_checkmark_validation established
        (editor stays open — compound: folder_name_input stays visible AND
        get_folder_item(folder_id) resolves to ZERO elements — input value
        unchanged, no PUT fires), matching this file's Axis-2 precedent
        that a single signal could pass even if some other unintended
        side effect fired.
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
                "Side-channel check — no unexpected console errors across "
                "the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename "
                    f"validation: {[m.text for m in console_messages]!r}"
                )

        finally:
            # Same caution as test_folder_rename_checkmark_validation's own
            # cleanup: FOLDER_MENU_DELETE_ITEM is a DEAD testid (regression
            # #1309, NOT this case's scope, reconfirmed dead during
            # ELITEA-2459 exploration). delete_folder_via_menu() now falls
            # back to a direct API delete when that testid doesn't appear,
            # so cleanup succeeds via that path while #1309 stays open —
            # this try/except remains only as a last-resort net.
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2121_chat-folder-rename-via-edit-option-in-context-menu.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_folder_rename_via_context_menu_edit_option(self, page):
        """ELITEA-2121 — Chat: Folder Rename via Edit Option in Context Menu.

        A near-total SUBSET of test_folder_rename_checkmark_validation
        (ELITEA-2458)'s own flow: open the rename editor via the dot-menu's
        Rename item, type ONE valid new name directly (no boundary-state
        probing — that's ELITEA-2458/2459's own territory), confirm, verify
        the PUT persists and the display updates. The one NEW element this
        case covers that ELITEA-2458 never does: asserting the context
        menu's own item set on open (Rename + Pin/Unpin present).

        **Depends on a regression fix landed THIS implementation** —
        FolderItem.jsx's dot-menu "Rename" item lost its `key`
        (chat-folder-menu-rename-menuitem testid) to an unrelated main-branch
        feature commit after ELITEA-2458 first added it. Re-confirmed via a
        live pre-fix run of test_folder_rename_checkmark_validation itself
        (this file's own sibling test) failing with a TimeoutError before
        the fix. Filed as
        https://github.com/EliteaAI/elitea-testing-public/issues/1533 and
        fixed on EliteaUI's automation/testids (commit be489cee) — this test
        would not pass without that fix.

        **Case-text drift** (case step 2 says the menu shows "Delete, Edit,
        Export, Pin or Unpin" — the real set is "New chat, Rename, Pin on
        top, Delete") filed as
        https://github.com/EliteaAI/elitea-testing-public/issues/1534. This
        test asserts the real, live-confirmed item set (Rename + Pin/Unpin
        by testid), not the case's literal list — per the project's
        reverse-masking guard, asserting a list the product doesn't actually
        show would be masking the drift, not proving the case.

        No fidelity substitution — every observable (menu content, editor
        pre-fill, PUT status, displayed name, console cleanliness) is read
        off the real system through the real dot-menu -> Rename UI flow.

        Spec: test-specs/chat-interface/lextend_folder-rename-via-context-menu-edit-option_ELITEA-2121.md
        """
        chat = ChatPage(page)
        folder_id = None
        seed_name = "ELITEA2121RenameSource"
        new_name = "New folder_edited"

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Step 1 — Seed a folder, hover its row; verify the 3-dot "
                "menu button becomes visible"
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
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                logger.info("Seeded folder %s named %r", folder_id, seed_name)

                # AFS step 1's own verify: hovering the folder row reveals
                # its 3-dot menu button (CSS-hover-revealed, scoped inside
                # chat-folder-item-{folder_id} per the AFS's Concrete
                # Handles table) — asserted HERE, not inferred from
                # open_folder_context_menu() succeeding in Step 2 below.
                folder_item.locator(chat.FOLDER_ICON).hover()
                folder_menu_button = folder_item.locator(chat.CONVERSATION_MENU_BUTTON).first
                expect(folder_menu_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Click the 3-dot icon; verify the context menu "
                "becomes visible and shows the real item set (Rename, "
                "Pin/Unpin) — NOT the case's drifted 'Delete, Edit, Export, "
                "Pin or Unpin' list, see #1534"
            ):
                chat.open_folder_context_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(page.locator(chat.FOLDER_CONTEXT_MENU_POPOVER)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                rename_item = page.locator(chat.FOLDER_MENU_RENAME_ITEM)
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                pin_item = page.locator(chat.FOLDER_MENU_PIN_ITEM)
                expect(pin_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_item.text_content() == "Pin on top", (
                    "Pin menu item should read 'Pin on top' for an "
                    f"unpinned folder, got: {pin_item.text_content()!r}"
                )

            with allure.step(
                "Step 3 — Click the Rename item; verify the inline editor "
                "opens pre-filled with the folder's current name"
            ):
                rename_item.click()
                chat.folder_name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == seed_name, (
                    f"Rename editor should be pre-filled with {seed_name!r}"
                )

            with allure.step(
                f"Step 4 — Clear the name and type {new_name!r}"
            ):
                chat.set_folder_name(new_name)
                assert chat.folder_name_input.input_value() == new_name, (
                    f"Input should show {new_name!r}"
                )

            with allure.step(
                "Step 5 — Click the checkmark icon; verify the rename "
                "persists server-side and the displayed name updates"
            ):
                assert chat.is_folder_name_confirm_enabled(), (
                    "Confirm checkmark should be active for a valid, "
                    "changed name"
                )
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
                assert new_name in (folder_item.text_content() or ""), (
                    f"Folder {folder_id} should display the renamed name {new_name!r}"
                )

            with allure.step(
                "Step 6 — Verify no error message is shown (no unexpected "
                "console errors across the full flow)"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename via "
                    f"context menu: {[m.text for m in console_messages]!r}"
                )

        finally:
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s via API", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2130_chat-pinned-folder-can-be-renamed.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_pinned_folder_rename_retains_pin_state(self, page):
        """ELITEA-2130 — Chat: Pinned Folder Can Be Renamed.

        Genuinely NEW gap vs ELITEA-2121/2458/2459: none of those ever pin a
        folder. Seeds a folder, pins it via the dot-menu's Pin item
        (NEW chat-folder-menu-pin-menuitem testid, added this
        implementation), renames it through the SAME dot-menu -> Rename ->
        checkmark flow, then re-asserts the folder is STILL pinned
        afterwards — proving the rename mutation doesn't reset
        meta.is_pinned server-side.

        Depends on the SAME https://github.com/EliteaAI/elitea-testing-public/issues/1533
        regression fix as ELITEA-2121 (shared first-interactive-step
        dependency). Also depends on a NEW `data-pinned` state attribute
        added to FolderAccordion.jsx's already-testid'd chat-folder-item-{id}
        element this implementation (mirrors ConversationItem.jsx's existing
        data-pinned convention) — the raw PinIcon the UI conditionally
        renders in the collapsed header carries no testid and isn't a
        sanctioned locator target per this project's state-via-data-*
        policy.

        Uses ChatPage.open_folder_context_menu()'s force-click (already
        required for a PINNED folder's dot-menu button — its
        DraggableFolderItem wrapper renders a genuinely HTML-disabled
        ancestor once pinned; a plain click times out even though the
        button's own `.disabled` property is false, confirmed live this
        session and recorded in test-specs/chat-interface/_surface.md).

        Case-text drift (same class as ELITEA-2121, filed together as
        https://github.com/EliteaAI/elitea-testing-public/issues/1534) —
        this test asserts the real item set including the "Unpin" label
        (not the case's literal "Delete, Edit, Export, Unpin" list).

        No fidelity substitution — pin state, rename, and pin-state
        persistence are all read off the real system through the real UI
        flow (PATCH for pin, PUT for rename, both awaited and status-checked).

        Spec: test-specs/chat-interface/lextend_pinned-folder-rename-retains-pin-state_ELITEA-2130.md
        """
        chat = ChatPage(page)
        folder_id = None
        seed_name = "ELITEA2130PinnedSource"
        new_name = "Pinned Renamed Folder"

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Step 1 — Seed a folder, pin it via the dot-menu's Pin "
                "item; verify data-pinned=\"true\""
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

                assert not chat.is_folder_pinned(folder_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded folder {folder_id} should not start pinned"
                )

                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as pin_response_info:
                    chat.pin_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_response = pin_response_info.value
                assert pin_response.status == 200, (
                    f"Pin PATCH should resolve 200, got {pin_response.status} "
                    f"for {pin_response.url}"
                )
                assert chat.is_folder_pinned(folder_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Folder {folder_id} should carry data-pinned=\"true\" "
                    "after pinning via the dot-menu"
                )

            with allure.step(
                "Step 2 — Hover the pinned folder, click its 3-dot icon; "
                "verify the context menu shows the real item set with "
                "'Unpin' (not the case's drifted list, see #1534)"
            ):
                chat.open_folder_context_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(page.locator(chat.FOLDER_CONTEXT_MENU_POPOVER)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                rename_item = page.locator(chat.FOLDER_MENU_RENAME_ITEM)
                expect(rename_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                pin_item = page.locator(chat.FOLDER_MENU_PIN_ITEM)
                expect(pin_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_item.text_content() == "Unpin", (
                    "Pin menu item should read 'Unpin' for an already-"
                    f"pinned folder, got: {pin_item.text_content()!r}"
                )

            with allure.step(
                "Step 3 — Click Rename; clear the name and type the new "
                "pinned-folder name"
            ):
                rename_item.click()
                chat.folder_name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == seed_name, (
                    f"Rename editor should be pre-filled with {seed_name!r}"
                )
                chat.set_folder_name(new_name)
                assert chat.folder_name_input.input_value() == new_name, (
                    f"Input should show {new_name!r}"
                )

            with allure.step(
                "Step 4 — Click the checkmark icon; verify the rename "
                "persists server-side and the displayed name updates"
            ):
                assert chat.is_folder_name_confirm_enabled(), (
                    "Confirm checkmark should be active for a valid, "
                    "changed name"
                )
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
                assert new_name in (folder_item.text_content() or ""), (
                    f"Folder {folder_id} should display the renamed name {new_name!r}"
                )

            with allure.step(
                "Step 5 — Verify the folder retains its pinned state "
                "(pin icon still visible) after the rename"
            ):
                assert chat.is_folder_pinned(folder_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Folder {folder_id} should still carry "
                    'data-pinned="true" after being renamed — the rename '
                    "must not reset the folder's pinned state"
                )

            with allure.step(
                "Step 6 — Verify no error message is shown (no unexpected "
                "console errors across the full flow)"
            ):
                assert not console_messages, (
                    "Unexpected console errors during pinned folder "
                    f"rename: {[m.text for m in console_messages]!r}"
                )

        finally:
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s via API", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2122_chat-folder-rename-cancel-via-x-icon-discards-changes.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_folder_rename_cancel_via_x_icon_discards_changes(self, page):
        """ELITEA-2122 — Chat: Folder Rename — Cancel via X Icon Discards Changes.

        The one folder-rename case element none of this file's existing
        tests (ELITEA-2458/2459/2121/2130) ever exercise: the CANCEL/X-icon
        path. All four only ever click the checkmark (confirm) or leave the
        editor untouched — grep for "cancel" across this file returns 0 hits
        before this test.

        ``FolderItem.jsx``'s cancel `Box`, for an EXISTING (non-new) folder,
        fires `handleOnCloseEditFolder`: `setFolderName(name)` +
        `setIsFolderEditing(false)` — pure local-state reset, no network
        call anywhere in the handler. Source-confirmed (not re-derived) —
        the exact same mechanism already independently live-verified twice
        on sibling components: `handleOnCancelCreateFolder`
        (`test_chat_folder_creation_custom_name_and_cancel.py`, ELITEA-2120)
        and `ConversationItem.jsx`'s cancel handler (ELITEA-2100). This test
        asserts the network-silence signal directly (zero new PUT requests)
        rather than relying on DOM-closure alone, so a hypothetical
        instant save-then-revert couldn't slip through as a false pass.

        Case-text drift (case step 1 says "click Edit" — the real menu item
        is labelled "Rename"), same drift already filed for the sibling
        ELITEA-2121/2130 cases as
        https://github.com/EliteaAI/elitea-testing-public/issues/1534 — not
        re-filed here, this test clicks the real "Rename" item.

        No fidelity substitution — every observable (editor pre-fill, input
        value, PUT-absence, displayed name, console cleanliness) is read off
        the real system through the real dot-menu -> Rename -> cancel UI flow.

        Spec: test-specs/chat-interface/lextend_chat-folder-rename-cancel-via-x-icon_ELITEA-2122.md
        """
        chat = ChatPage(page)
        folder_id = None
        seed_name = "ELITEA2122RenameCancelSource"
        temp_name = "Renamed Folder"

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        # Tracks every PUT to the folder-update endpoint fired during the
        # whole test — step 3 asserts NO new entry appears across the
        # cancel-click, same network-silence idiom as this file's own
        # inactive-checkmark no-op checks (steps 3/6 of
        # test_folder_rename_checkmark_validation above).
        put_requests = []

        def _on_request(request):
            if request.method == "PUT" and "/folder/prompt_lib/" in request.url:
                put_requests.append(request.url)

        page.on("request", _on_request)

        try:
            with allure.step(
                "Step 1 — Navigate to Chats, hover a folder, click the "
                "3-dot icon, click Rename (case says 'Edit' — see #1534); "
                "verify the folder name is editable"
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
                assert chat.folder_name_input.input_value() == seed_name, (
                    f"Rename editor should be pre-filled with {seed_name!r}"
                )

            with allure.step(
                f"Step 2 — Clear the current name and type {temp_name!r}; "
                "verify the new name appears in the input"
            ):
                chat.set_folder_name(temp_name)
                assert chat.folder_name_input.input_value() == temp_name, (
                    f"Input should show {temp_name!r}"
                )

            with allure.step(
                "Step 3 — Click the X (cancel) icon; verify the input "
                "closes WITHOUT saving (editor gone + zero new PUT requests)"
            ):
                puts_before = len(put_requests)
                chat.folder_name_cancel_button.click()
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on a "
                    f"cancel-icon click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                "Step 4 — Verify the folder still displays its original "
                "name (not the discarded, never-saved temp name)"
            ):
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                folder_item_text = folder_item.text_content() or ""
                assert seed_name in folder_item_text, (
                    f"Folder {folder_id} should still display its original "
                    f"name {seed_name!r}, got: {folder_item_text!r}"
                )
                assert temp_name not in folder_item_text, (
                    f"Folder {folder_id} must NOT display the discarded "
                    f"cancelled name {temp_name!r}, got: {folder_item_text!r}"
                )

            with allure.step(
                "Step 5 — Verify no error message is shown (no unexpected "
                "console errors across the full flow)"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename "
                    f"cancel: {[m.text for m in console_messages]!r}"
                )

        finally:
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s via API", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2131_chat-folder-rename-no-changes-made-checkmark-inactive.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_folder_rename_no_changes_close_via_x_icon(self, page):
        """ELITEA-2131 — Chat: Folder Rename — No Changes Made, Checkmark
        Inactive, Close via X Icon.

        Steps 1-4 restate test_folder_rename_checkmark_validation
        (ELITEA-2458/2125)'s own Step 6 mechanism ("valid but unchanged"
        state — FolderItem.jsx's isFolderSaveEnabled is a pure string
        comparison at render time, so "restore the original value" and
        "never touch the field" are behaviourally identical, source-
        confirmed). The genuinely NEW element (steps 5-6) is closing the
        editor via the X (cancel) icon with ZERO edits ever made, then
        re-reading the folder's displayed NAME IN THE LIST (not just the
        editor's own local state) — neither
        test_folder_rename_checkmark_validation (never clicks cancel) nor
        test_folder_rename_cancel_via_x_icon_discards_changes (ELITEA-2122,
        cancels only AFTER typing a different name first) exercises this
        exact "cancel with no prior edits" combination.

        Spec: test-specs/chat-interface/lextend_folder-rename-no-changes-close-via-x_ELITEA-2131.md
        """
        chat = ChatPage(page)
        folder_id = None
        seed_name = "ELITEA2131NoChangesSource"

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
                "Step 1 — Seed a folder, open its rename editor via the "
                "dot-menu; verify the input is pre-filled with the "
                "folder's current name"
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
                assert chat.folder_name_input.input_value() == seed_name, (
                    f"Rename editor should be pre-filled with {seed_name!r}"
                )

            with allure.step(
                "Step 2 — Do not make any changes to the folder name; "
                "verify it is still unchanged"
            ):
                assert chat.folder_name_input.input_value() == seed_name, (
                    "Input should still show the unchanged original name"
                )

            with allure.step(
                "Step 3 — Verify the checkmark icon is disabled/inactive "
                "for the unchanged, valid name"
            ):
                assert not chat.is_folder_name_confirm_enabled(), (
                    'chat-folder-name-confirm-button should carry '
                    'data-disabled="true" for a valid-but-unchanged name'
                )

            with allure.step(
                "Step 4 — Attempt to click the checkmark icon; verify it "
                "has no effect"
            ):
                puts_before = len(put_requests)
                chat.folder_name_confirm_button.click()
                page.wait_for_timeout(300)
                assert chat.folder_name_input.is_visible(), (
                    "Editor should stay open after clicking the inactive "
                    "(unchanged) checkmark"
                )
                assert chat.folder_name_input.input_value() == seed_name, (
                    "Input should still show the unchanged original name"
                )
                assert chat.get_folder_item(folder_id).count() == 0, (
                    f"Folder {folder_id} should NOT re-render as an "
                    "accordion row — that would mean edit mode exited "
                    "unexpectedly"
                )
                assert len(put_requests) == puts_before, (
                    "No PUT to the folder endpoint should fire on an "
                    f"inactive-checkmark click, saw: {put_requests[puts_before:]}"
                )

            with allure.step(
                "Step 5 — Click the X (cancel) icon to close the edit "
                "mode; verify it closes with no network effect"
            ):
                puts_before_cancel = len(put_requests)
                chat.folder_name_cancel_button.click()
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)
                assert len(put_requests) == puts_before_cancel, (
                    "No PUT to the folder endpoint should fire on a "
                    f"cancel-icon click, saw: {put_requests[puts_before_cancel:]}"
                )

            with allure.step(
                "Step 6 — Verify the folder name is unchanged in the "
                "folder list"
            ):
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                folder_item_text = folder_item.text_content() or ""
                assert seed_name in folder_item_text, (
                    f"Folder {folder_id} should still display its "
                    f"original name {seed_name!r}, got: {folder_item_text!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across "
                "the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder rename with "
                    f"no changes made: {[m.text for m in console_messages]!r}"
                )

        finally:
            if folder_id:
                try:
                    chat.delete_folder_via_api(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)


class TestChatFolderDeleteApiFallbackRegression:
    """Regression coverage for the ``ChatPage.delete_folder_via_api()``
    cleanup fallback added to ``delete_folder_via_menu()``
    (EliteaAI/elitea-testing-public#1309).

    Root cause this guards against: ``delete_folder_via_menu()``'s dot-menu
    "Delete" item testid (``FOLDER_MENU_DELETE_ITEM``) has regressed dead on
    EliteaUI three times; every call site uses the method purely for
    cleanup wrapped in a bare ``try``/``except``, so the timeout was
    swallowed silently and cleanup never happened — #1309 confirmed 19
    "New folder"/"New folder6" folders leaked into the shared DEV project
    this way, making every subsequent folder-list refetch progressively
    more fragile. The fix added an API-delete fallback; THIS test exercises
    ``delete_folder_via_api()`` directly, independent of whether #1309 is
    fixed upstream or not, so a regression in the fallback's own request
    (wrong URL, wrong auth, or a response check that doesn't actually
    verify deletion) is caught even once the dot-menu path stops needing it.
    """

    @pytest.mark.p2
    def test_delete_folder_via_api_actually_removes_the_folder(self, page):
        """``delete_folder_via_api()`` must make the folder actually
        disappear server-side — not just return without raising.

        A regression that reproduces the ORIGINAL #1309 failure mode (an
        exception silently swallowed, or a "success" response that isn't
        checked) must fail this test: the ground truth is a full page
        RELOAD re-reading the folder list from the server, not the absence
        of a raised exception.
        """
        chat = ChatPage(page)
        folder_id = None

        try:
            with allure.step(
                "Step 1 — Seed a folder to delete via the API fallback"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()

                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                    timeout=NAVIGATION_TIMEOUT,
                ) as create_response_info:
                    chat.set_folder_name("APIFallbackDeleteRegressionTest")
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
                logger.info("Seeded folder %s for API-fallback delete regression test", folder_id)

            with allure.step(
                "Step 2 — Call delete_folder_via_api() directly (bypassing "
                "the UI dot-menu entirely)"
            ):
                chat.delete_folder_via_api(folder_id, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Reload and verify the folder is GONE via a fresh "
                "server-backed read (ground truth, not just 'no exception')"
            ):
                page.reload()
                chat.wait_for_page_load()
                expect(chat.get_folder_item(folder_id)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                # Deletion succeeded — don't attempt it again in `finally`.
                folder_id = None
        finally:
            # Best-effort net only: if Step 2/3 itself failed (the folder
            # was never actually deleted), fall back to the dot-menu path
            # so this test doesn't ALSO leak a folder while proving the
            # leak-prevention fix.
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
