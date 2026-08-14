"""UI Test for ELITEA-2091 — Chat: Create New Conversation from Team Project
with File Attachments (Picker + Drag-and-Drop) and Changing LLM.

Verifies that, in a Team project, a new conversation can be created with
files attached via BOTH the file-picker and drag-and-drop, the LLM can be
switched to a non-default model, and the conversation is auto-named after
the first exchange.

Spec: test-specs/chat-interface/l2_create-new-conversation-team-project-attachments-and-llm_ELITEA-2091.md

Testid gap filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@dd417746):
- ``chat-composer-dropzone`` — the outer drop-zone ``Box`` in
  ``UserInput.jsx`` (wraps ``onDragOver``/``onDragLeave``/``onDrop``)
  previously carried no testid at all (AFS § Concrete Handles).

New page-object surface (``ChatPage``, all additive):
- ``model_selector_name`` / ``MODEL_SELECTOR_OPTION`` / dynamic
  ``MODEL_SELECTOR_OPTION_ANY_SELECTOR`` — the composer's own instance of
  the shared ``LLMModelSelector``/``LLMModelsMenu`` widget already exposed
  on ``AgentDetailPage``/``PipelineDetailPage``/``SkillDetailPage``/
  ``ToolkitTestSettingsPage`` was previously only reachable via the outer
  ``model_selector`` field.
- ``get_model_option_suffixes()`` / ``get_selected_model_option_suffix()`` /
  ``is_model_option_selected()`` / ``select_llm_model_by_suffix()`` /
  ``close_model_selector()``.
- ``composer_dropzone`` + ``drag_and_drop_file()`` — synthetic
  ``DataTransfer``-based drag-and-drop technique (see docstring on the
  method itself; declared per AFS § Automation Hints / fidelity policy —
  substitutes only the OS-drag input mechanism, not the observable).
- ``get_conversation_item_in_group()`` — raw Locator for a conversation
  item scoped inside a date-group, for reading its own text/state (the
  "Naming" placeholder -> real-title transition).

Live exploration this implementation (localhost, project 471): confirmed
the plus-menu popper stays open across a picker file-chooser selection
(counter reads "Attach Files10 left" -> "Attach Files7 left" for 3 files,
then "Attach Files6 left" after the drag-and-drop addition); confirmed the
synthetic-DataTransfer drag-and-drop technique renders a 4th chip
identically to the picker-attached ones; confirmed ``Mui-selected``
transfers to the newly-selected model option on reopening the dropdown;
confirmed the auto-naming resolution and the message thread carrying all 4
attached filenames. No product defects found — see AFS § Known Defects
Found.

Usage:
    cd automation
    pytest tests/ui/chat/test_create_new_conversation_team_project_attachments_and_llm.py -v
"""

import logging
import re

import allure
import pytest
from api import ConversationAPI
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
# Case step 10: auto-naming resolves "within ~15s" — a slightly wider
# ceiling absorbs normal LLM-latency variance without changing what's
# asserted (AFS § Test Steps step 10).
NAMING_RESOLVE_TIMEOUT = 20_000

# Team project — the ONLY environment where the plus-menu's "Invite Users"
# item renders at all (PlusChatButton.jsx's `!isPrivateProject` guard —
# AFS § Preconditions / case step 2). No shared TEAM_PROJECT_ID constant
# module exists yet across chat tests (checked
# test_open_conversation_today_section.py,
# test_team_users_mention_and_remove_participants.py,
# test_invite_users_add_cancel_close.py — each defines its own local
# copy; following the same convention here rather than introducing a
# shared module unilaterally, per AFS § Test Data).
TEAM_PROJECT_ID = "471"

FIRST_MESSAGE = "Please review the attached documents"

# Expected top-level plus-menu items on a Team project, besides "Attach
# Files" (which uses a distinct testid, chat-attach-menuitem-button,
# outside the shared "-menuitem" suffix family counted by
# ChatPage.get_open_plus_menu_item_count()) — Modules, Agents, Pipelines,
# Toolkits, MCPs, Invite Users (AFS § Test Steps step 2).
EXPECTED_PLUS_MENU_ITEM_COUNT = 6


def _is_known_project_471_secrets_403(msg) -> bool:
    """Filter the pre-existing, already-documented project-471 ``secrets`` 403.

    Project 471 ("Elitea Testing Team") surfaces a ``403 Forbidden`` on
    ``GET .../secrets/secrets/default/471`` on every page load, regardless
    of any action taken — an environment/permission-scoping artifact of
    that specific project, not a symptom of anything this case's
    automation touches (AFS § Network Behavior; same idiom as
    ``test_open_conversation_today_section.py``'s
    ``_is_known_project_471_secrets_403``). Matched on both the message
    text and the request location URL so a genuinely NEW 403 elsewhere
    isn't accidentally swallowed by a text-only match.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default/471" in (text + location_url)


class TestCreateNewConversationTeamProjectAttachmentsAndLLM:
    """ELITEA-2091: Chat — Team Project — Create New Conversation with File
    Attachments (picker + drag-drop) and Changing LLM (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2091_create-new-conversation-from-team-project-with-file-attachments-and-changing-llm.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_conversation_team_project_attachments_and_llm(self, page, _browser_cookies, tmp_path):
        """Create a Team-project conversation with picker + drag-drop
        attachments and a switched LLM; verify auto-naming.

        Steps (AFS
        test-specs/chat-interface/l2_create-new-conversation-team-project-attachments-and-llm_ELITEA-2091.md):
        1. Switch to the Team project (471); click "+Chat".
        2. Click the plus-menu button; verify the exact item set incl.
           "Invite Users" (Team-project-only signal).
        3. Click "Attach Files"; verify the native file chooser opens.
        4. Select 3 files in one chooser action; verify chips + counter.
        5. Drag-and-drop 1 more file onto the composer; verify identical
           rendering.
        6. Click the model selector; verify the dropdown lists every model.
        7. Select a different LLM; verify Mui-selected + composer trigger.
        8. Type the message; verify it appears.
        9. Send; verify the message + all 4 attachments in the thread, URL.
        10. Verify the new conversation under "Today", Naming -> real title.
        """
        team_conversation_api = ConversationAPI(
            browser_cookies=_browser_cookies, project_id=TEAM_PROJECT_ID,
        )
        conv_id = None
        chat = ChatPage(page)

        # Registered before Step 1 so console errors from every step are
        # captured. The known, already-documented project-471 secrets 403
        # (AFS § Network Behavior) is filtered so it can't mask a genuinely
        # NEW error on the same project. `pageerror` catches an uncaught JS
        # exception, which `console` alone would miss (same dual-listener
        # idiom as `test_open_conversation_today_section.py`).
        console_messages = []
        page_errors: list[str] = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_project_471_secrets_403(msg):
                console_messages.append(msg)

        def _on_pageerror(exc):
            page_errors.append(str(exc))

        page.on("console", _on_console)
        page.on("pageerror", _on_pageerror)

        attached_file_names: list[str] = []

        try:
            with allure.step(
                "Step 1 — Switch to the Team project; click +Chat; verify a "
                "new blank conversation opens"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.switch_project(TEAM_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)

                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                assert chat.message_input.is_visible(), (
                    "Message input should be visible in the new blank conversation"
                )
                assert chat.is_input_empty(), (
                    "Message input should be empty right after starting a "
                    "fresh conversation via +Chat"
                )

            with allure.step(
                "Step 2 — Click the plus-menu button; verify the popper "
                "shows the exact item set, including Invite Users"
            ):
                chat.open_attach_menuitem(timeout=UI_ELEMENT_TIMEOUT)

                attach_text = chat.attach_files_button.text_content() or ""
                assert "10 left" in attach_text, (
                    f"'Attach Files' should show '10 left' for a fresh "
                    f"conversation, got: {attach_text!r}"
                )

                assert chat.internal_tools_menuitem.is_visible(), "Modules item should be visible"
                assert chat.agents_menuitem.is_visible(), "Agents item should be visible"
                assert chat.pipelines_menuitem.is_visible(), "Pipelines item should be visible"
                assert chat.toolkits_menuitem.is_visible(), "Toolkits item should be visible"
                assert chat.mcps_menuitem.is_visible(), "MCPs item should be visible"
                # This is the case's own structural signal that the test
                # actually ran against a Team project, not the default
                # Private one (Invite Users is absent entirely — not merely
                # disabled — on Private; AFS § Coverage Map Axis 2).
                assert chat.invite_users_menuitem.is_visible(), (
                    "Invite Users should render for a Team project"
                )

                item_count = chat.get_open_plus_menu_item_count()
                assert item_count == EXPECTED_PLUS_MENU_ITEM_COUNT, (
                    f"Expected exactly {EXPECTED_PLUS_MENU_ITEM_COUNT} "
                    f"top-level plus-menu items (Modules, Agents, Pipelines, "
                    f"Toolkits, MCPs, Invite Users), got {item_count}"
                )

            with allure.step(
                "Step 3 — Click 'Attach Files'; verify the native file "
                "chooser opens"
            ):
                # Clicking plus_menu_button again (e.g. via
                # open_file_chooser()/attach_files_via_menu()) would TOGGLE
                # the already-open popper CLOSED (ELITEA-2203-documented
                # quirk) — click attach_files_button directly instead, the
                # popper opened by Step 2 is still open.
                with page.expect_file_chooser(timeout=UI_ELEMENT_TIMEOUT) as fc_info:
                    chat.attach_files_button.click()
                file_chooser = fc_info.value

            with allure.step(
                "Step 4 — Select 3 files in ONE chooser action; verify each "
                "renders as a chip and the counter decrements by 3"
            ):
                picker_names = [f"elitea_2091_pick_{i}.txt" for i in range(1, 4)]
                picker_paths = []
                for name in picker_names:
                    f = tmp_path / name
                    f.write_text(f"ELITEA-2091 picker attachment {name} unique-token.")
                    picker_paths.append(str(f))

                file_chooser.set_files(picker_paths)
                chat.wait_for_network(timeout=UI_ELEMENT_TIMEOUT)

                # Total = visible chips + overflow — the plus-menu popper
                # being open narrows the composer, so FileList.jsx's
                # visible/overflow split is container-width-dependent
                # (never hardcode a "N visible" split; same reasoning as
                # ChatPage.get_total_attached_file_count()'s docstring).
                assert chat.get_total_attached_file_count() == 3, (
                    "Expected 3 total attached files after the picker selection"
                )

                # Read the counter text BEFORE get_all_attached_file_names():
                # when an overflow bucket exists, that helper opens the
                # overflow Menu and closes it via Escape — a KEY that MUI
                # also propagates to the PARENT plus-menu Popper, closing
                # the whole popper (confirmed live this session). Reading
                # the still-testid'd trigger first avoids racing that.
                attach_text_after_picker = chat.attach_files_button.text_content() or ""
                assert "7 left" in attach_text_after_picker, (
                    f"'Attach Files' counter should read '7 left' after "
                    f"attaching 3 of 10, got: {attach_text_after_picker!r}"
                )

                all_names = chat.get_all_attached_file_names()
                for name in picker_names:
                    assert name in all_names, (
                        f"Expected attachment {name!r}, got: {all_names}"
                    )
                attached_file_names.extend(picker_names)

            with allure.step(
                "Step 5 — Drag and drop 1 additional file onto the composer; "
                "verify it appears identically to a picker-attached file"
            ):
                drop_name = "elitea_2091_drop_1.txt"
                drop_path = tmp_path / drop_name
                drop_path.write_text("ELITEA-2091 drag-and-drop attachment unique-token.")

                total_count_before_drop = chat.get_total_attached_file_count()
                chat.drag_and_drop_file(str(drop_path), timeout=UI_ELEMENT_TIMEOUT)

                assert chat.get_total_attached_file_count() == total_count_before_drop + 1, (
                    "Expected exactly one additional attached file after the drag-and-drop"
                )

                # Same ordering rationale as Step 4 — read the counter text
                # BEFORE get_all_attached_file_names(), which can close the
                # whole plus-menu popper via its internal Escape-key press
                # when an overflow bucket exists.
                attach_text_after_drop = chat.attach_files_button.text_content() or ""
                assert "6 left" in attach_text_after_drop, (
                    f"'Attach Files' counter should read '6 left' after the "
                    f"drag-and-drop addition, got: {attach_text_after_drop!r}"
                )

                all_names_after_drop = chat.get_all_attached_file_names()
                assert drop_name in all_names_after_drop, (
                    f"Expected the dropped file {drop_name!r} among attachments, "
                    f"got: {all_names_after_drop}"
                )
                attached_file_names.append(drop_name)

                # "Structurally identical" (case step 5) — the dropped
                # file is read via the SAME get_all_attached_file_names()
                # helper (visible CHAT_ATTACHMENT_CHIP + overflow
                # CHAT_ATTACHMENT_OVERFLOW_ITEM prefixes) as the
                # picker-attached ones — no separate/different locator
                # exists for a "dropped" attachment; whichever bucket
                # (visible/overflow) it renders into is exactly the same
                # container-width-driven split FileList.jsx applies to
                # every attachment regardless of how it was added.

                # get_all_attached_file_names() may have already closed the
                # plus-menu popper as a side effect (its overflow-menu
                # Escape press also closes the PARENT popper — the
                # documented ELITEA-2203 quirk, see
                # ChatPage.close_plus_menu_popper()'s docstring). Leave the
                # popper in a known-closed state via the SAFE method (never
                # Escape directly — same quirk) before moving on.
                if chat.attach_files_button.count() > 0:
                    chat.close_plus_menu_popper(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6 — Click the model selector; verify the dropdown "
                "lists every available model"
            ):
                chat.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                option_suffixes = chat.get_model_option_suffixes(timeout=UI_ELEMENT_TIMEOUT)
                assert option_suffixes, "Model dropdown should list at least one option"

            with allure.step(
                "Step 7 — Select a different LLM; verify it is shown "
                "selected (Mui-selected + checkmark) and reflected in the "
                "composer trigger"
            ):
                current_suffix = chat.get_selected_model_option_suffix(timeout=UI_ELEMENT_TIMEOUT)
                assert current_suffix, (
                    "Exactly one model option should carry Mui-selected before switching"
                )
                previous_model_display_name = (chat.model_selector_name.text_content() or "").strip()

                # Resolve at runtime and avoid the environment's
                # deliberately-broken smoke-test model entries (name
                # containing "Broken", seeded for error-path testing
                # elsewhere) — selecting one here would make Step 10's
                # auto-naming LLM call fail for a reason unrelated to this
                # case (AFS § Test Data — do not hardcode a display name).
                candidates = [
                    suffix for suffix in option_suffixes
                    if suffix != current_suffix and "broken" not in suffix.lower()
                ]
                assert candidates, (
                    "Expected at least one non-current, non-broken model "
                    f"option to switch to among: {option_suffixes}"
                )
                target_suffix = candidates[0]

                chat.select_llm_model_by_suffix(target_suffix, timeout=UI_ELEMENT_TIMEOUT)
                # The composer trigger's text updates one React render tick
                # after the click closes the dropdown — wait for it rather
                # than racing a one-shot read (ChatPage docstring).
                chat.wait_for_selected_model_name_change(
                    previous_model_display_name, timeout=UI_ELEMENT_TIMEOUT
                )

                new_model_display_name = (chat.model_selector_name.text_content() or "").strip()
                assert new_model_display_name, (
                    "Composer trigger should show a non-empty model name after switching"
                )
                assert new_model_display_name != previous_model_display_name, (
                    f"Composer trigger should show the NEWLY selected model, "
                    f"replacing the previous one — still shows: {new_model_display_name!r}"
                )

                # Reopen the dropdown — the just-selected option should now
                # carry Mui-selected. Source-confirmed (LLMModelsMenu.jsx):
                # the identical boolean condition
                # (`item.id === selectedModel?.id`) that sets Mui-selected
                # also gates the CheckedIcon checkmark's render — same
                # element, no separate testid (AFS § Test Steps step 7) —
                # so this is the testid-only-compliant proof of "selected
                # LLM shown with a checkmark".
                chat.open_model_selector(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_model_option_selected(target_suffix, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Option {target_suffix!r} should carry Mui-selected "
                    "after being selected"
                )
                chat.close_model_selector(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 8 — Type the message into the input; verify it appears"):
                chat.message_input.fill(FIRST_MESSAGE)
                assert (chat.message_input.input_value() or "").strip() == FIRST_MESSAGE, (
                    "Message input should show the typed text"
                )

            with allure.step(
                "Step 9 — Send (Enter); verify the message + all 4 "
                "attachments appear in the thread, URL updates"
            ):
                chat.message_input.press("Enter", timeout=60000)
                chat.wait_for_input_ready(timeout=NAVIGATION_TIMEOUT)

                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                match = re.search(r"/chat/(\d+)", page.url)
                assert match, f"Conversation id should appear in the URL, got: {page.url}"
                conv_id = int(match.group(1))
                assert "name=" in page.url, (
                    f"URL should carry a '?name=...' query param after "
                    f"send, got: {page.url}"
                )

                chat.wait_for_message_count(1, timeout=UI_ELEMENT_TIMEOUT)
                sent_message_text = chat.messages_container.nth(0).text_content() or ""
                assert FIRST_MESSAGE in sent_message_text, (
                    "The sent user message should carry the typed text"
                )
                assert len(attached_file_names) == 4, "Sanity: 3 picker + 1 drag-drop = 4"
                for name in attached_file_names:
                    assert name in sent_message_text, (
                        f"Expected attachment {name!r} listed under the "
                        f"sent message, got: {sent_message_text!r}"
                    )

            with allure.step(
                "Step 10 — Verify a new conversation appears under 'Today'; "
                "the 'Naming' placeholder resolves to a genuine title"
            ):
                assert chat.is_conversation_group_visible("today", timeout=UI_ELEMENT_TIMEOUT), (
                    "'Today' date-group heading should be visible in the sidebar"
                )
                assert chat.is_conversation_in_group(conv_id, "today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render under the Today group"
                )

                chat.wait_for_naming_label_to_resolve(timeout=NAMING_RESOLVE_TIMEOUT)

                conversation_item = chat.get_conversation_item_in_group(conv_id, "today")
                resolved_title = (conversation_item.text_content() or "").strip()
                assert resolved_title, (
                    "Conversation item should render a genuine (non-empty) title"
                )
                # LLM titling is non-deterministic — assert only that the
                # placeholder is gone and a real title took its place
                # (AFS § Test Steps step 10), never the exact string.
                assert "Naming" not in resolved_title, (
                    "Conversation title should no longer show the 'Naming' "
                    f"placeholder, got: {resolved_title!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors or "
                "uncaught exceptions across the full flow"
            ):
                assert not console_messages and not page_errors, (
                    f"Unexpected side-channel errors: "
                    f"console={[m.text for m in console_messages]!r} "
                    f"page_errors={page_errors!r}"
                )

        finally:
            if conv_id:
                try:
                    team_conversation_api.delete_conversation(int(conv_id))
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
