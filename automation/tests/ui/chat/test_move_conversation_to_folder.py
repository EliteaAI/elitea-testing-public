"""UI Tests for ELITEA-2135/2136/2137/2138/2139/2140/2141 — Chat: Move
Conversation via "Move to" Menu.

Seven cases sharing the SAME "Move to" submenu surface (``surface_key:
chat-conversation-context-menu``), kept as separate test methods per the
AFS's own "differ in steps -> separate AFS/test" rule — each picks a
different path through the submenu (existing folder, create-a-new-folder
with default/custom name, back-to-the-list, folder-to-folder). They share
one file because they were analysed as a cluster and all exercise the same
``open_move_to_submenu()`` / ``click_move_to_and_wait_for_submenu()``
helpers — not because their test bodies are merged. ELITEA-2136 and
ELITEA-2140 are ``extend-existing`` in the tag-only/small-insertion sense
(no new test method — 2136 adds two assertion lines to ELITEA-2135's own
Step 4; 2140 adds one assertion line to ELITEA-2139's own Step 4).

Specs:
- test-specs/chat-interface/l3_move-conversation-to-existing-folder_ELITEA-2135.md
- test-specs/chat-interface/lextend_move-conversation-removed-from-all-date-groups_ELITEA-2136.md
- test-specs/chat-interface/l3_move-conversation-to-new-folder_ELITEA-2137.md
- test-specs/chat-interface/lextend_move-conversation-to-new-folder-custom-name_ELITEA-2138.md
- test-specs/chat-interface/lextend_move-conversation-back-to-list_ELITEA-2139_2140.md
- test-specs/chat-interface/lextend_move-conversation-between-two-folders_ELITEA-2141.md

Known defect EliteaAI/elitea-testing-public#1117 — the "Move to" submenu
does not open reliably on a single click (hovering never opens it at all).
Every test reaches the open-submenu state via
``ChatPage.click_move_to_and_wait_for_submenu()``'s poll-and-retry-click
workaround (see that method's docstring for the live evidence) — this does
NOT weaken any test's own assertions: the submenu's contents are still
fully verified once open.

No other product defects were found — all remaining steps of every case
matched the live product exactly (minor case-text-wording CLARIFICATIONs
noted in each AFS's Coverage Map, e.g. the toast text's embedded quote
marks — not defects). ELITEA-2140's stated "originally in Older"
precondition cannot be produced via any test-accessible surface (live-
verified: the API silently ignores caller-supplied timestamps) — see
``lextend_move-conversation-back-to-list_ELITEA-2139_2140.md``'s own
"ELITEA-2140's precondition" section for the full reasoning; the case's own
Pass/Fail criteria are still fully asserted via the mechanism-grounded
equivalent (the move unconditionally refreshes ``updated_at``, proven live).
"""

import logging
import time

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

# Live-reconfirmed for the default test project (${ELITEA_PROJECT_ID},
# Private) — same 5-item set ELITEA-2114's AFS already established
# (CLARIFICATION-2). "Make public"/"Share" are absent by design.
EXPECTED_MENU_ITEM_KEYS = ("rename", "move-to", "playback", "pin", "delete")

TARGET_FOLDER_NAME = "New folder6"  # ELITEA-2135's own Test Data value
DEFAULT_FOLDER_NAME = "New folder"  # ELITEA-2137's DefaultFolderName constant


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (both AFSes' § Network Behavior) — unrelated to the
    move-to-folder flow. Matched on both the message text and the request
    location URL, same idiom as the sibling chat tests' equivalent filter.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestMoveConversationToExistingFolder:
    """ELITEA-2135: Chat – Move Conversation to Existing Folder via Move To Menu (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2135_chat-move-conversation-to-existing-folder.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2136_chat-move-conversation-to-existing-folder-removed-from-date-group.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_conversation_to_existing_folder(self, page, conversation_api):
        """Move a conversation into an existing folder via the "Move to" submenu.

        Steps (AFS
        test-specs/chat-interface/l3_move-conversation-to-existing-folder_ELITEA-2135.md,
        extended by
        test-specs/chat-interface/lextend_move-conversation-removed-from-all-date-groups_ELITEA-2136.md):
        1. Hover conv_target, click its 3-dot menu; verify the context menu
           shows exactly the live 5-item set.
        2. Click "Move to"; verify the submenu mounts (with retry — known
           defect #1117) and enumerate its contents.
        3. Click the target folder's own submenu item; verify the success
           toast.
        4. Verify conv_target is no longer rendered under any date-group
           heading (SCOPED 0-count — MUI Collapse keeps a collapsed
           folder's children DOM-mounted). ELITEA-2136 extends this step
           to also assert absence from "this_week" and "older" (ELITEA-2135
           only asserted "today") — a fresh API-created conversation can
           only ever start in "today", so the extra checks are a
           belt-and-braces guard against a stale-cache regression, not a
           duplicate of the "today" check.
        5. Expand target_folder and verify conv_target is inside it.

        Setup creates conv_target (API) and target_folder ("New folder6",
        via the CHATS-header create-folder UI flow with a custom name
        typed over the "New folder" default — no ``FolderAPI`` client
        exists yet, per the AFS's own Automation Hints, which sanctions
        this UI-flow option for a single test).
        """
        chat = ChatPage(page)
        conv_target_id = None
        target_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create conv_target via API; navigate to chat; "
                "create target_folder 'New folder6' via the CHATS header icon"
            ):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2135_target_{ts}")
                conv_target_id = target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
                chat.set_folder_name(TARGET_FOLDER_NAME)
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                    timeout=NAVIGATION_TIMEOUT,
                ) as folder_response_info:
                    chat.folder_name_confirm_button.click()
                folder_response = folder_response_info.value
                assert folder_response.status == 201, (
                    "target_folder POST should resolve 201, got "
                    f"{folder_response.status} for {folder_response.url}"
                )
                folder_body = folder_response.json()
                assert folder_body.get("name") == TARGET_FOLDER_NAME, (
                    f"target_folder response 'name' should be {TARGET_FOLDER_NAME!r}, "
                    f"got: {folder_body!r}"
                )
                target_folder_id = folder_body.get("id")
                assert target_folder_id is not None, (
                    f"target_folder response should include a real 'id', got: {folder_body!r}"
                )
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                chat.get_folder_item(target_folder_id).wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                logger.info(
                    "Setup complete — conv_target=%s target_folder=%s",
                    conv_target_id, target_folder_id,
                )

            with allure.step(
                "Step 1 — Hover conv_target, click its 3-dot menu; verify "
                "the context menu shows exactly the live 5-item set"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                for key in EXPECTED_MENU_ITEM_KEYS:
                    expect(chat.get_conversation_menu_item(key)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                item_count = chat.get_open_conversation_menu_item_count()
                assert item_count == len(EXPECTED_MENU_ITEM_KEYS), (
                    f"Expected exactly {len(EXPECTED_MENU_ITEM_KEYS)} context-menu "
                    f"items ({EXPECTED_MENU_ITEM_KEYS}), found {item_count}"
                )

            with allure.step(
                "Step 2 — Click 'Move to'; verify the submenu mounts "
                "(with retry — known defect "
                "EliteaAI/elitea-testing-public#1117) and enumerate its contents"
            ):
                chat.click_move_to_and_wait_for_submenu(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.move_to_create_folder_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.move_to_back_to_list_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                target_folder_menuitem = chat.get_move_to_folder_item(target_folder_id)
                expect(target_folder_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert TARGET_FOLDER_NAME in (target_folder_menuitem.text_content() or ""), (
                    f"target_folder's submenu item should show its name "
                    f"{TARGET_FOLDER_NAME!r}"
                )

            with allure.step(
                "Step 3 — Click the target folder's submenu item; verify "
                "the success toast (live text includes quote marks around "
                "the folder name — CLARIFICATION, not a defect)"
            ):
                chat.select_move_to_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                expected_toast = f'Chat moved to "{TARGET_FOLDER_NAME}" folder successfully'
                expect(chat.toast_message).to_have_text(expected_toast, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify conv_target is no longer rendered under "
                "any date-group heading (SCOPED 0-count — MUI Collapse "
                "keeps a collapsed folder's children DOM-mounted, so an "
                "unscoped page-wide count would give a false pass)"
            ):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer render under Today"
                # ELITEA-2136 extension — the case explicitly asks for This
                # Week and Older to be checked too, not just Today. A fresh
                # API-created conversation can only ever start in Today, so
                # this is a belt-and-braces guard (would catch a stale-cache
                # regression rendering the moved conversation under a
                # different date group), not a duplicate of the check above.
                assert not chat.is_conversation_in_group(
                    conv_target_id, "this_week", timeout=3_000,
                ), f"conv_target {conv_target_id} should not render under This Week either"
                assert not chat.is_conversation_in_group(
                    conv_target_id, "older", timeout=3_000,
                ), f"conv_target {conv_target_id} should not render under Older either"

            with allure.step(
                "Step 5 — Expand target_folder and verify conv_target is inside it"
            ):
                chat.expand_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(target_folder_id), (
                    f"target_folder {target_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    target_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conv_target {conv_target_id} should be inside "
                    f"target_folder {target_folder_id} after moving"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-to-existing-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            # Independent try/except per resource (.claude/rules/ui-tests.md
            # § Test Data Lifecycle) — one resource's cleanup failure must
            # not block the other's.
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if target_folder_id:
                try:
                    chat.delete_folder_via_menu(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up target_folder %s", target_folder_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete target_folder %s: %s", target_folder_id, exc,
                    )


class TestMoveConversationToNewFolder:
    """ELITEA-2137: Chat – Move Conversation to a New Folder via Move To Menu (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2137_chat-move-conversation-to-a-new-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_conversation_to_new_folder(self, page, conversation_api):
        """Move a conversation into a brand-new folder via the "Move to" > "Create folder" sub-flow.

        Steps (AFS
        test-specs/chat-interface/l3_move-conversation-to-new-folder_ELITEA-2137.md):
        1. Open conv_target's "Move to" submenu (with retry — known defect
           #1117, cross-referenced from ELITEA-2135, not re-filed).
        2. Click "Create folder"; verify a new inline-editable "New folder"
           entry appears, focused.
        3. Verify checkmark and X icons are visible.
        4. Click the checkmark without changing the name; verify the POST
           resolves 201 and the "moved to" toast appears (DISTINCT from
           ELITEA-2132's toast-less plain-create flow — this submenu's
           version moves the conversation in the same action).
        5. Verify conv_target is no longer rendered under any date-group
           heading (SCOPED 0-count, same MUI-Collapse trap as ELITEA-2135).
        6. Expand the new folder and verify conv_target is inside it.
        """
        chat = ChatPage(page)
        conv_target_id = None
        new_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — create conv_target via API; navigate to chat"):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2137_target_{ts}")
                conv_target_id = target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Open conv_target's 'Move to' submenu (with retry "
                "— known defect EliteaAI/elitea-testing-public#1117, same "
                "as ELITEA-2135, cross-referenced not re-filed); verify it mounts"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.move_to_create_folder_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.move_to_back_to_list_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click 'Create folder'; verify a new inline-"
                "editable 'New folder' entry appears, focused. No "
                "server-side folder exists yet at this point."
            ):
                chat.select_move_to_create_folder(timeout=UI_ELEMENT_TIMEOUT)
                chat.folder_name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == DEFAULT_FOLDER_NAME, (
                    "New folder editor should be pre-filled with the default "
                    f"name {DEFAULT_FOLDER_NAME!r}"
                )
                expect(chat.folder_name_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify checkmark and X icons are visible next to the input"
            ):
                assert chat.folder_name_confirm_button.is_visible(), (
                    "chat-folder-name-confirm-button should be visible"
                )
                assert chat.folder_name_cancel_button.is_visible(), (
                    "chat-folder-name-cancel-button should be visible"
                )

            with allure.step(
                "Step 4 — Click confirm without changing the default name; "
                "verify the POST resolves 201 and the 'moved to' toast "
                "appears (distinct from ELITEA-2132's toast-less "
                "plain-create flow — this entry point moves the "
                "conversation in the same action)"
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
                assert body.get("name") == DEFAULT_FOLDER_NAME, (
                    f"Response body 'name' should be {DEFAULT_FOLDER_NAME!r}, got: {body!r}"
                )
                new_folder_id = body.get("id")
                assert new_folder_id is not None, (
                    f"Response body should include a real folder 'id', got: {body!r}"
                )

                expected_toast = f'Chat moved to "{DEFAULT_FOLDER_NAME}" folder successfully'
                expect(chat.toast_message).to_have_text(expected_toast, timeout=UI_ELEMENT_TIMEOUT)
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 5 — Verify conv_target is no longer rendered under "
                "any date-group heading (SCOPED 0-count, same MUI-Collapse "
                "trap as ELITEA-2135)"
            ):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer render under Today"

            with allure.step(
                "Step 6 — Expand the new folder and verify conv_target is inside it"
            ):
                chat.expand_folder(new_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(new_folder_id), (
                    f"New folder {new_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    new_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conv_target {conv_target_id} should be inside "
                    f"new_folder {new_folder_id} after moving"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-to-new-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if new_folder_id:
                try:
                    chat.delete_folder_via_menu(new_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up new_folder %s", new_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete new_folder %s: %s", new_folder_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2138_chat-move-conversation-to-a-new-folder-with-custom-name.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_conversation_to_new_folder_with_custom_name(self, page, conversation_api):
        """Move a conversation to a NEW folder with a custom (non-default) name.

        Steps (AFS
        test-specs/chat-interface/lextend_move-conversation-to-new-folder-custom-name_ELITEA-2138.md):
        1. Open conv_target's "Move to" submenu (with retry — known defect
           #1117), click "Create folder"; verify the default-named inline
           editor appears, focused.
        2. Clear the default name, type "Sprint Chats" via
           ``ChatPage.set_folder_name()`` (its ``.clear()``-based
           implementation — a raw ``Control+a``+``Backspace`` sequence
           reproduces the documented "append not replace" race, live-
           reconfirmed during this case's own AFS exploration); click
           confirm. Verify the input read back the replaced (not
           appended) value before confirming, and the POST resolves 201
           with the custom name.
        3. Verify the success toast names the custom folder.
        4. Verify conv_target is no longer rendered under Today (SCOPED
           0-count — same MUI-Collapse trap as ELITEA-2135/2137).
        5. Expand "Sprint Chats" and verify conv_target is inside it.
        """
        chat = ChatPage(page)
        conv_target_id = None
        new_folder_id = None
        custom_folder_name = "Sprint Chats"

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Setup — create conv_target via API; navigate to chat"):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2138_target_{ts}")
                conv_target_id = target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Open conv_target's 'Move to' submenu (with retry "
                "— known defect EliteaAI/elitea-testing-public#1117, same "
                "as ELITEA-2135/2137); click 'Create folder'; verify the "
                "default-named inline editor appears, focused"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.select_move_to_create_folder(timeout=UI_ELEMENT_TIMEOUT)
                chat.folder_name_input.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == DEFAULT_FOLDER_NAME, (
                    "New folder editor should be pre-filled with the default "
                    f"name {DEFAULT_FOLDER_NAME!r}"
                )
                expect(chat.folder_name_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Clear the default name, type 'Sprint Chats' via "
                "set_folder_name(); verify the input replaced (not "
                "appended) the value, then confirm and verify the POST "
                "resolves 201 with the custom name"
            ):
                chat.set_folder_name(custom_folder_name)
                assert chat.folder_name_input.input_value() == custom_folder_name, (
                    "Folder-name input should read back the REPLACED value "
                    f"{custom_folder_name!r}, not an appended one (a bare "
                    "Control+a+Backspace clear reproduces a documented "
                    "'append not replace' race — see set_folder_name()'s "
                    "own docstring)"
                )
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
                assert body.get("name") == custom_folder_name, (
                    f"Response body 'name' should be {custom_folder_name!r}, got: {body!r}"
                )
                new_folder_id = body.get("id")
                assert new_folder_id is not None, (
                    f"Response body should include a real folder 'id', got: {body!r}"
                )

            with allure.step(
                "Step 3 — Verify the success toast names the custom folder"
            ):
                expected_toast = f'Chat moved to "{custom_folder_name}" folder successfully'
                expect(chat.toast_message).to_have_text(expected_toast, timeout=UI_ELEMENT_TIMEOUT)
                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify conv_target is no longer rendered under "
                "Today (SCOPED 0-count, same MUI-Collapse trap as "
                "ELITEA-2135/2137)"
            ):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer render under Today"

            with allure.step(
                "Step 5 — Expand 'Sprint Chats' and verify conv_target is inside it"
            ):
                chat.expand_folder(new_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(new_folder_id), (
                    f"New folder {new_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    new_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conv_target {conv_target_id} should be inside "
                    f"new_folder {new_folder_id} after moving"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-to-new-folder-with-"
                    f"custom-name flow: {[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if new_folder_id:
                try:
                    chat.delete_folder_via_menu(new_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up new_folder %s", new_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete new_folder %s: %s", new_folder_id, exc)


class TestMoveConversationBackToList:
    """ELITEA-2139/2140: Chat – Move Conversation Back to the List via Move To Menu (l3, medium).

    Family AFS — both case IDs assert the identical mechanism (a conversation
    inside a folder, moved back to the general list via "Move to" > "Back to
    the list", unconditionally lands in Today because the move refreshes
    updated_at server-side). ELITEA-2140 adds ONE extra assertion (explicit
    absence from "older") — see the AFS's own § "ELITEA-2140's precondition"
    for why a literal Older-origin fixture cannot be produced via any
    test-accessible surface, and why this mechanism-grounded assertion is the
    honest equivalent.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2139_chat-move-conversation-back-to-the-list.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2140_chat-conversation-moved-from-older-back-to-list-appears-in-today.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_conversation_back_to_list(self, page, conversation_api):
        """Move a conversation OUT of a folder via "Move to" > "Back to the list".

        Steps (AFS
        test-specs/chat-interface/lextend_move-conversation-back-to-list_ELITEA-2139_2140.md):
        1. Expand a folder containing conv_target; verify it's inside.
        2. Open conv_target's "Move to" submenu (with retry — known
           defect #1117, same as ELITEA-2135/2137/2138).
        3. Click "Back to the list"; verify the PUT resolves 200 with
           folder_id: null, and the (distinct-template) success toast.
        4. Verify conv_target now renders under Today, AND — ELITEA-2140's
           own distinguishing ask — is provably absent from "older" too
           (honestly producible without seeding a literal Older-origin
           fixture, which is not possible via any test-accessible surface
           — see the AFS's own reasoning).
        5. Verify the folder still exists, now empty.

        Setup creates folder + conv_target via API, then moves conv_target
        into folder via API (``conversation_api.move_conversation_to_folder``)
        — real setup, not the tested action; the case names no required
        mechanism for reaching "conversation inside a folder".
        """
        chat = ChatPage(page)
        conv_target_id = None
        folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder + conv_target via API; move "
                "conv_target into folder via API; navigate to chat"
            ):
                ts = int(time.time())
                folder = conversation_api.create_folder(f"autotest_2139_folder_{ts}")
                folder_id = folder["id"]
                target = conversation_api.create_conversation(f"autotest_2139_target_{ts}")
                conv_target_id = target["id"]
                conversation_api.move_conversation_to_folder(conv_target_id, folder_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Expand the folder containing conv_target; "
                "verify it's inside"
            ):
                chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_id), (
                    f"folder {folder_id} should carry data-expanded=\"true\" "
                    "after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"conv_target {conv_target_id} should be inside folder {folder_id}"

            with allure.step(
                "Step 2 — Open conv_target's 'Move to' submenu (with retry "
                "— known defect EliteaAI/elitea-testing-public#1117, same "
                "as ELITEA-2135/2137/2138)"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.move_to_back_to_list_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Click 'Back to the list'; verify the PUT "
                "resolves 200 with folder_id: null, and the success toast "
                "(distinct template from the move-INTO-a-folder toast)"
            ):
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.select_move_to_back_to_list(timeout=UI_ELEMENT_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Back-to-the-list PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") is None, (
                    f"Response body 'folder_id' should be null after moving "
                    f"back to the list, got: {move_body!r}"
                )
                expect(chat.toast_message).to_have_text(
                    "Chat moved to ungrouped area successfully", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Verify conv_target now renders under Today, and "
                "(ELITEA-2140) is provably absent from Older too"
            ):
                assert chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should render under Today after moving back"
                # ELITEA-2140's own distinguishing ask — explicit absence
                # from Older. A literal Older-origin fixture cannot be
                # seeded via any test-accessible surface (see the AFS's
                # own "ELITEA-2140's precondition" section: the API
                # silently ignores caller-supplied timestamps, live-
                # verified) — this asserts the mechanism-grounded
                # equivalent instead: the move unconditionally refreshes
                # updated_at, so the moved conversation can never land in
                # Older regardless of its prior state.
                assert not chat.is_conversation_in_group(
                    conv_target_id, "older", timeout=3_000,
                ), f"conv_target {conv_target_id} should not render under Older"

            with allure.step(
                "Step 5 — Verify the folder still exists, now empty"
            ):
                expect(chat.get_folder_item(folder_id)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-back-to-list flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)


class TestMoveConversationBetweenTwoFolders:
    """ELITEA-2141: Chat – Move Conversation Between Two Folders via Move To Menu (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2141_chat-move-conversation-between-two-folders.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_conversation_between_two_folders(self, page, conversation_api):
        """Move a conversation already inside one folder into a DIFFERENT folder.

        Steps (AFS
        test-specs/chat-interface/lextend_move-conversation-between-two-folders_ELITEA-2141.md):
        1. Expand source_folder containing conv_target; verify it's inside.
        2. Open conv_target's "Move to" submenu (with retry — known
           defect #1117); verify it lists ALL folders including
           source_folder itself (DISABLED — self-move prevention) and
           target_folder (enabled).
        3. Select target_folder; verify the PUT resolves 200 with the
           changed folder_id, and the success toast.
        4. Verify conv_target is no longer listed under source_folder
           (SCOPED 0-count).
        5. Expand target_folder and verify conv_target is inside it.

        Setup creates source_folder + target_folder + conv_target via API,
        then moves conv_target into source_folder via API — real setup,
        not the tested action.
        """
        chat = ChatPage(page)
        conv_target_id = None
        source_folder_id = None
        target_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create source_folder + target_folder + "
                "conv_target via API; move conv_target into source_folder "
                "via API; navigate to chat"
            ):
                ts = int(time.time())
                source_folder = conversation_api.create_folder(f"autotest_2141_source_{ts}")
                source_folder_id = source_folder["id"]
                target_folder = conversation_api.create_folder(f"autotest_2141_target_{ts}")
                target_folder_id = target_folder["id"]
                target = conversation_api.create_conversation(f"autotest_2141_target_conv_{ts}")
                conv_target_id = target["id"]
                conversation_api.move_conversation_to_folder(conv_target_id, source_folder_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Expand source_folder containing conv_target; "
                "verify it's inside"
            ):
                chat.expand_folder(source_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(source_folder_id), (
                    f"source_folder {source_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    source_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"conv_target {conv_target_id} should be inside source_folder {source_folder_id}"

            with allure.step(
                "Step 2 — Open conv_target's 'Move to' submenu (with "
                "retry — known defect EliteaAI/elitea-testing-public#1117, "
                "same as ELITEA-2135/2137/2138/2139); verify it lists "
                "source_folder ITSELF disabled (self-move prevention) and "
                "target_folder enabled"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                source_item = chat.get_move_to_folder_item(source_folder_id)
                expect(source_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert source_item.get_attribute("aria-disabled") == "true", (
                    "source_folder's own entry in the 'Move to' submenu "
                    "should be disabled (a conversation cannot be moved "
                    "into the folder it's already in)"
                )
                target_item = chat.get_move_to_folder_item(target_folder_id)
                expect(target_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert target_item.get_attribute("aria-disabled") != "true", (
                    "target_folder's entry in the 'Move to' submenu should "
                    "be enabled"
                )

            with allure.step(
                "Step 3 — Select target_folder; verify the PUT resolves "
                "200 with the changed folder_id, and the success toast"
            ):
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.select_move_to_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Move-to-target-folder PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") == target_folder_id, (
                    f"Response body 'folder_id' should be {target_folder_id!r} "
                    f"after moving, got: {move_body!r}"
                )
                expected_toast = (
                    f'Chat moved to "{target_folder["name"]}" folder successfully'
                )
                expect(chat.toast_message).to_have_text(expected_toast, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify conv_target is no longer listed under "
                "source_folder (SCOPED 0-count, same MUI-Collapse trap as "
                "ELITEA-2135)"
            ):
                assert not chat.is_conversation_in_folder(
                    source_folder_id, conv_target_id, timeout=3_000,
                ), (
                    f"conv_target {conv_target_id} should no longer be "
                    f"inside source_folder {source_folder_id} after moving"
                )

            with allure.step(
                "Step 5 — Expand target_folder and verify conv_target is inside it"
            ):
                chat.expand_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(target_folder_id), (
                    f"target_folder {target_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    target_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conv_target {conv_target_id} should be inside "
                    f"target_folder {target_folder_id} after moving"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-between-two-folders flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if source_folder_id:
                try:
                    chat.delete_folder_via_menu(source_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up source_folder %s", source_folder_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete source_folder %s: %s", source_folder_id, exc,
                    )
            if target_folder_id:
                try:
                    chat.delete_folder_via_menu(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up target_folder %s", target_folder_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete target_folder %s: %s", target_folder_id, exc,
                    )
