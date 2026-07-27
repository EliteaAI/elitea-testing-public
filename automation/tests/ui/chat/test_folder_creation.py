"""UI Test for ELITEA-2132 — Chat: Folder Creation via CHATS Header Icon.

Verifies the CHATS panel header folder-creation icon: clicking it inserts an
inline, editable "New folder" entry with checkmark/cancel affordances;
confirming with the default name creates a real folder server-side
(``POST .../folder/prompt_lib/{project_id}`` -> ``201``) and renders it as a
collapsed accordion item with a folder icon, expand arrow, and the name "New
folder"; expanding the folder shows the "No conversations added" empty
state.

Spec: test-specs/chat-interface/l3_chat-folder-creation-via-chats-header-icon_ELITEA-2132.md

This is the first test to cover chat folders — ``test_conversation_
management.py``'s own module docstring states P2 folders/sharing were
explicitly out of scope before this case (`TC-CONV-001 through TC-CONV-007
(P0/P1 only; P2 folders/sharing skipped)`), and the whole "Folders" feature
area had zero ``data-testid`` coverage before the analyst pass for this
case. 8 testids were added during analysis (commit 6fceb3e2 on
``automation/testids``); a 9th (the folder dot-menu's "Delete" item) was
added during this implementation — ``FolderItem.jsx``'s ``menuItems`` had no
``key`` field, so the shared ``DotMenu``/``BasicMenuItem`` machinery (which
already derives a testid from ``item.key``, confirmed via
``ConversationItem.jsx``'s sibling items) never emitted one. See
``ChatPage.FOLDER_MENU_DELETE_ITEM`` and ``delete_folder_via_menu()``.

No product defects were found — all 7 case steps matched the live product
exactly, including the literal empty-state wording "No conversations added".

Fix-only round 2 (reviewer CHANGES_REQUESTED — Coverage Map over-claim,
SUPERSEDED by round 3 below): the original Step 3 block asserted the
new-folder input's default value and focus, but never proved the entry
actually renders ABOVE pre-existing content. Round 2 fixed this by seeding a
conversation (via the ``conversation_id`` fixture) and comparing the new
entry's position against the "Today" date-group heading.

Fix-only round 3 (reviewer CHANGES_REQUESTED — round 2's fix didn't close
the gap): round 2's folder-vs-conversation-heading comparison only proved
that the Folders section renders above the Conversations section — a
DOM/layout fact that's unconditionally true (``Conversations.jsx`` always
mounts the Folders container before the Conversations container, regardless
of folder count or order) and would stay green even if a regression made
new folders get APPENDED to the bottom of the folder list instead of
PREPENDED to the top, because the test only ever had 0 pre-existing folders
to compare against (cleanup runs after every test). Fixed by seeding one
real BASELINE folder — via the exact header-icon + confirm-default-name
flow the case itself exercises — before Step 3 runs, so there is a genuine
sibling folder in the list, then asserting the new editor renders ABOVE
*that folder's own row*: folder-vs-folder, not folder-vs-conversation-
heading. Manually verified live before writing this fix: creating a first
folder, then triggering the create-folder flow a second time, lands the new
input's bounding box (``y=71,height=24`` → bottom 95) above the baseline
folder row's box (``y=106``) — the same shape of proof the reviewer used
(``chat-folder-item-6`` at ``y=56`` above ``chat-folder-item-5`` at
``y=97``) to confirm the product correctly prepends. The round-2 seeded
conversation / ``get_conversation_group_header()`` comparison is dropped —
superseded, not needed alongside the stronger check, and dropping it halves
the seeded state this test now carries. ``ChatPage.get_conversation_group_
header()`` itself is left in place (additive, harmless, may be useful to a
future test) even though this test no longer calls it. Both folders (the
baseline and the case's own) are deleted in the ``finally`` block.
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

DEFAULT_FOLDER_NAME = "New folder"
EMPTY_STATE_TEXT = "No conversations added"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior — same artifact already documented
    in the ELITEA-2114/ELITEA-2095/ELITEA-1893 AFSes) — unrelated to folder
    creation. Matched on both the message text and the request location URL
    (same idiom as the sibling chat tests' equivalent filter) so a genuinely
    NEW 403 elsewhere isn't accidentally swallowed.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestChatFolderCreation:
    """ELITEA-2132: Chat – Folder Creation via CHATS Header Icon (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2132_chat-folder-creation-via-chats-header-icon.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_create_folder_via_chats_header_icon(self, page):
        """Create a folder via the CHATS header icon, confirm with the
        default name, and verify its collapsed + expanded rendering.

        Steps (AFS
        test-specs/chat-interface/l3_chat-folder-creation-via-chats-header-icon_ELITEA-2132.md):
        1. Navigate to chat; verify the CHATS panel is displayed.
        2. Verify the folder-creation icon is visible, positioned before
           the search button.
        3. Click it; verify a new, focused, editable "New folder" entry
           appears at the top of the folder list, ABOVE a real sibling
           BASELINE folder's own row (folder-vs-folder positional
           bounding-box check — fix-only round 3; see module docstring).
        4. Verify the confirm (checkmark) and cancel (X) icons are visible.
        5. Click confirm without changing the name; verify the underlying
           POST resolves 201 with the expected response shape, and the
           folder item appears collapsed (data-expanded="false").
        6. Verify the folder icon and expand arrow are both present, and
           the name reads "New folder".
        7. Expand the folder; verify data-expanded flips to "true" and the
           "No conversations added" empty state is shown.

        A baseline folder is seeded (same header-icon + confirm-default-name
        flow the case itself exercises) between Step 2 and Step 3 — not a
        numbered case step, purely an Axis-2 addition so Step 3's position
        check has a real sibling folder to compare against. Both the
        baseline and the case's own folder are deleted in the ``finally``
        block.
        """
        chat = ChatPage(page)
        folder_id = None
        baseline_folder_id = None

        # Registered before Setup so console errors from every step are
        # captured (side-channel discipline — silent errors are the worst
        # bugs). The known, environment-wide secrets 403 noise (see
        # _is_known_secrets_403) is filtered so it can't mask a genuinely
        # new error.
        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Navigate to chat; verify the CHATS panel is displayed"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                assert chat.conversations_panel_heading.is_visible(), (
                    "'Chats' heading should be visible in the left panel"
                )

            with allure.step(
                "Step 2 — Verify the folder-creation icon is visible and "
                "positioned before the search button"
            ):
                assert chat.create_folder_button.is_visible(), (
                    "chat-create-folder-button should be visible in the CHATS header"
                )
                assert chat.search_conversations_button.is_visible(), (
                    "Search conversations button should be visible as the "
                    "positional anchor for step 2"
                )
                create_box = chat.create_folder_button.bounding_box()
                search_box = chat.search_conversations_button.bounding_box()
                assert create_box is not None and search_box is not None, (
                    "Both the create-folder icon and search button should "
                    "have a resolvable bounding box"
                )
                assert create_box["x"] < search_box["x"], (
                    "chat-create-folder-button should render to the LEFT of "
                    f"the search button — create_box={create_box}, "
                    f"search_box={search_box}"
                )

            # --- Setup: seed one baseline folder (not a numbered case step) ---
            # Round-3 review finding: comparing the new-folder entry against
            # the "Today" conversation date-group heading (round 2's fix)
            # only proves the Folders section renders above the
            # Conversations section — a DOM/layout fact that's
            # unconditionally true regardless of folder order, so it would
            # stay green even if a regression appended new folders to the
            # BOTTOM of the folder list instead of prepending them to the
            # top. Seeding a real sibling folder here, via the exact flow
            # the case itself exercises, gives Step 3 something genuine to
            # compare position against.
            chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
            with page.expect_response(
                lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "POST",
                timeout=NAVIGATION_TIMEOUT,
            ) as baseline_response_info:
                chat.folder_name_confirm_button.click()
            baseline_response = baseline_response_info.value
            assert baseline_response.status == 201, (
                "Baseline folder POST should resolve 201, got "
                f"{baseline_response.status} for {baseline_response.url}"
            )
            baseline_folder_id = baseline_response.json().get("id")
            assert baseline_folder_id is not None, (
                "Baseline folder response should include a real 'id', got: "
                f"{baseline_response.json()!r}"
            )
            chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
            chat.get_folder_item(baseline_folder_id).wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT
            )
            logger.info("Seeded baseline folder %s", baseline_folder_id)

            with allure.step(
                "Step 3 — Click the folder-creation icon; verify a new, "
                "focused, editable 'New folder' entry appears ABOVE the "
                "baseline folder (folder-vs-folder position check)"
            ):
                chat.click_create_folder_button(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.folder_name_input.input_value() == DEFAULT_FOLDER_NAME, (
                    "New folder editor should be pre-filled with the "
                    f"default name {DEFAULT_FOLDER_NAME!r}"
                )
                expect(chat.folder_name_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)

                # Positional check (round-3 review finding): compare against
                # the BASELINE FOLDER's own row, not a conversation
                # date-group heading. This is the comparison that actually
                # distinguishes "prepended to the top" from "appended to
                # the bottom", since both folders live in the same list —
                # the conversation-heading comparison couldn't, because
                # Folders always renders above Conversations regardless of
                # folder order.
                input_box = chat.folder_name_input.bounding_box()
                baseline_box = chat.get_folder_item(baseline_folder_id).bounding_box()
                assert input_box is not None and baseline_box is not None, (
                    "Both the new-folder input and the baseline folder row "
                    "should have a resolvable bounding box — "
                    f"input_box={input_box}, baseline_box={baseline_box}"
                )
                assert input_box["y"] + input_box["height"] <= baseline_box["y"], (
                    "New folder entry should render ABOVE the baseline "
                    f"folder (id={baseline_folder_id}) — i.e. prepended to "
                    "the top of the folder list, not appended below it — "
                    f"input_box={input_box}, baseline_folder_box={baseline_box}"
                )

            with allure.step(
                "Step 4 — Verify the confirm (checkmark) and cancel (X) "
                "icons are visible next to the input"
            ):
                assert chat.folder_name_confirm_button.is_visible(), (
                    "chat-folder-name-confirm-button should be visible"
                )
                assert chat.folder_name_cancel_button.is_visible(), (
                    "chat-folder-name-cancel-button should be visible"
                )

            with allure.step(
                "Step 5 — Click confirm without changing the default name; "
                "verify the POST resolves 201 with the expected response "
                "shape, and the folder editor closes"
            ):
                # This is the CASE's OWN folder (the second one created in
                # this run) — distinct from `baseline_folder_id` seeded
                # above for Step 3's position check.
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
                    f"Response body 'name' should be {DEFAULT_FOLDER_NAME!r}, "
                    f"got: {body!r}"
                )
                assert body.get("meta") == {}, (
                    f"Response body 'meta' should be an empty object, got: {body!r}"
                )
                folder_id = body.get("id")
                assert folder_id is not None, (
                    f"Response body should include a real folder 'id', got: {body!r}"
                )
                assert body.get("owner_id") is not None, (
                    f"Response body should include a real 'owner_id', got: {body!r}"
                )

                chat.folder_name_input.wait_for(state="hidden", timeout=UI_ELEMENT_TIMEOUT)
                folder_item = chat.get_folder_item(folder_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_folder_expanded(folder_id), (
                    f"Newly created folder {folder_id} should render collapsed "
                    "(data-expanded=\"false\")"
                )

            with allure.step(
                "Step 6 — Verify the folder displays a folder icon and "
                "expand arrow, and the name reads 'New folder'"
            ):
                folder_item = chat.get_folder_item(folder_id)
                assert folder_item.locator(chat.FOLDER_ICON).is_visible(), (
                    f"chat-folder-icon should be visible inside folder {folder_id}"
                )
                assert folder_item.locator(chat.FOLDER_EXPAND_ICON).is_visible(), (
                    f"chat-folder-expand-icon should be visible inside folder {folder_id}"
                )
                assert DEFAULT_FOLDER_NAME in (folder_item.text_content() or ""), (
                    f"Folder {folder_id} should display the name "
                    f"{DEFAULT_FOLDER_NAME!r}"
                )

            with allure.step(
                "Step 7 — Expand the folder; verify data-expanded flips to "
                "'true' and the empty state is shown"
            ):
                chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_id), (
                    f"Folder {folder_id} should carry data-expanded=\"true\" "
                    "after being clicked"
                )
                empty_state = folder_item.locator(chat.FOLDER_EMPTY_STATE)
                assert empty_state.is_visible(), (
                    f"chat-folder-empty-state should be visible inside "
                    f"expanded folder {folder_id}"
                )
                assert empty_state.text_content() == EMPTY_STATE_TEXT, (
                    f"Empty-state text should read {EMPTY_STATE_TEXT!r}, got: "
                    f"{empty_state.text_content()!r}"
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
            # Every run creates TWO real folders in the shared project — the
            # baseline (seeded above for Step 3's position check) and the
            # case's own (created by the actual flow under test) — cleanup
            # of BOTH is mandatory, not optional (AFS § Cleanup, round-3
            # amendment). No FolderAPI client exists yet (only
            # ConversationAPI et al. — AFS § Automation Hints recommends
            # adding one), so cleanup goes through the UI Delete flow, which
            # is fully testid-covered end to end. Each delete is
            # independently wrapped in try/except per
            # .claude/rules/ui-tests.md § Test Data Lifecycle — cleanup must
            # not mask the real test result, and one folder's delete
            # failure must not prevent attempting the other's.
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
            if baseline_folder_id:
                try:
                    chat.delete_folder_via_menu(baseline_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up baseline folder %s", baseline_folder_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete baseline folder %s: %s",
                        baseline_folder_id,
                        exc,
                    )
