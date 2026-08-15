"""UI Tests for Chat search filters and Modules panel toggles (ELITEA-2162,
extended by ELITEA-2464 and ELITEA-2463), plus the search-gap family
(ELITEA-2163/2164/2165).

Verifies the search icon opens a search field, partial and full-name queries
filter the conversation list, clicking a result opens the conversation, and
the Modules panel (+ -> Modules, hover) shows 10 toggleable modules that
persist via a confirmation toast — and that only an outside click (not
Escape) closes the panel. ELITEA-2464 extends this with: the full plus-menu
popup (6 top-level options), every module toggle exercised (not just 2
sampled), an explicit no-error-toast check, and a main-conversation-view-
restored check after closing the panel. ELITEA-2463 extends it further with:
a pinned conversation proving search results genuinely separate pinned from
date-grouped tiers, an explicit non-matching-conversation-absent check, and a
date-group-scoped exact-match check.

ELITEA-2163/2164/2165 are separate test methods on the same class, covering
the search no-results state, the X/clear icon closing search and restoring
the default view, and deleting characters dynamically re-filtering (growing)
the result set down to the full unfiltered list.

Markers:
    - ui: requires browser
    - p1: high priority (case priority "high" -> p1 pytest marker convention)
    - p3: medium priority (case priority "medium" -> p3 pytest marker convention)
    - chat: chat-related tests
    - regression: regression suite

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_search_and_modules_panel.py -v
"""

import logging
from uuid import uuid4

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 10000
NETWORK_RESPONSE_TIMEOUT = 10000


class TestChatSearchAndModulesPanel:
    """ELITEA-2162: Chat search filters conversations, opens result, Modules panel toggles work."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2162_chat-search-icon-opens-search-input-and-returns-partial-results-then-access-modules.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2464_chat-modules-panel-accessible-from-icon-in-conversation-with.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2463_chat-search-input-opens-filters-results-dynamically-conversation-is-interactable.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_search_filters_and_modules_panel_toggles(self, page, conversation_api):
        """Search icon filters conversations by partial/exact query, opens a
        result, and the Modules panel's toggles persist with a confirmation
        toast; closing works via outside click only (not Escape).

        ELITEA-2464 extension: full plus-menu popup verified before opening
        Modules, every module toggle exercised (not just 2 sampled), an
        explicit no-error-toast check per toggle, and the main conversation
        view (composer) verified restored after closing the panel.

        ELITEA-2463 extension: a pinned sibling conversation proves search
        results genuinely separate the pinned tier from date-grouped tiers
        (both filtered by the same query, live-confirmed via
        useQueryFoldersList's single shared backend call); the partial-query
        step also asserts a non-matching sibling is absent; the exact-match
        step additionally asserts the match renders inside its correct date
        group (not just "visible somewhere")."""
        conv_name = f"AutomationUnique{uuid4().hex[:8]}"
        sibling_conv_name = f"AutomationOther{uuid4().hex[:8]}"

        with allure.step("Setup — create a conversation with a unique name via API"):
            conv = conversation_api.create_conversation(conv_name)
            conv_id = str(conv["id"])
            logger.info("Created conversation %s (%s)", conv_id, conv_name)

        with allure.step(
            "Setup (ELITEA-2463 extension) — create a non-matching sibling "
            "conversation via API, for the pinned-grouping and "
            "non-match-absence assertions"
        ):
            sibling_conv = conversation_api.create_conversation(sibling_conv_name)
            sibling_conv_id = str(sibling_conv["id"])
            logger.info("Created sibling conversation %s (%s)", sibling_conv_id, sibling_conv_name)

        try:
            with allure.step("Step 1 — Navigate to chat; verify search icon visible"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                expect(chat.search_conversations_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1b (ELITEA-2463 extension) — Pin the sibling conversation "
                "via its context menu"
            ):
                chat.open_conversation_context_menu(sibling_conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_pinned(sibling_conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Sibling conversation {sibling_conv_id} should be pinned after the "
                    "'Pin on top' action"
                )

            with allure.step("Step 2 — Click search icon; verify input focused + clear icon visible"):
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_clear_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Type partial query 'un'; verify the generated conversation appears"):
                chat.type_conversation_search_query("un", timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # ELITEA-2463 extension (case step 7) — a conversation that does
                # NOT contain "un" must be absent from the partial-query results,
                # not merely "the target is present".
                expect(chat.get_conversation_item(sibling_conv_id)).not_to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3b (ELITEA-2463 extension) — Query for the pinned sibling's "
                "own prefix; verify search results separate the pinned tier from "
                "the date-grouped tier"
            ):
                chat.type_conversation_search_query("AutomationOther", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_conversation_pinned(sibling_conv_id, timeout=UI_ELEMENT_TIMEOUT), (
                    "Sibling conversation should still read as pinned while search-filtered"
                )
                expect(chat.get_conversation_item(sibling_conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # NOTE: no need to restore the "un" query here — Step 4 below
                # immediately replaces the query with the exact full name via
                # the same type_conversation_search_query() call (select-all +
                # retype), so the current query value doesn't matter. An
                # earlier version of this step re-typed "un" here, but that
                # exact string was already fetched (and cached) by the
                # original Step 3 moments earlier, so no new network response
                # ever fired and the wait timed out (live-confirmed).

            with allure.step("Step 4 — Type the exact full-name query; verify exactly one matching row"):
                chat.type_conversation_search_query(conv_name, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item_rows()).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # ELITEA-2463 extension (case step 9) — the match must render
                # INSIDE its correct date group, not merely "visible somewhere".
                assert chat.is_conversation_in_group(conv_id, group="today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should render inside the 'Today' date "
                    "group for the exact-match search result"
                )

            with allure.step("Step 5 — Click the matching conversation; verify it opens"):
                chat.click_conversation_item(conv_id, timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_conversation_url(conv_id, timeout=NAVIGATION_TIMEOUT)
                expect(chat.new_conversation_greeting).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6a (ELITEA-2464 extension) — Click + icon; verify the full "
                "popup menu shows all 6 options before opening Modules"
            ):
                chat.plus_menu_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.plus_menu_button.click()
                expect(chat.attach_files_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.internal_tools_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.agents_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.pipelines_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.toolkits_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.mcps_menuitem).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # NOTE: get_open_plus_menu_item_count() is scoped to the shared
                # `-menuitem` testid SUFFIX (PLUS_MENU_ITEM_SUFFIX), which
                # `chat-attach-menuitem-button` does not match (it ends in
                # `-menuitem-button`, a distinct naming convention for that one
                # control) — live-confirmed it returns 5, not 6. The 6 explicit
                # per-item visibility checks above are the real assertion for
                # "all 6 options visible"; this count corroborates the other 5.
                assert chat.get_open_plus_menu_item_count() == 5, (
                    "Plus-menu popup should show exactly 5 role=menuitem-suffixed "
                    "items (Modules, Agents, Pipelines, Toolkits, MCPs) alongside "
                    "the separately-verified Attach Files button"
                )

            with allure.step("Step 6 — Hover Modules menuitem to open Modules panel; verify 10 toggles in order"):
                chat.internal_tools_menuitem.hover()
                chat.verify_module_toggle_order(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6b (ELITEA-2464 extension) — Verify each toggle displays "
                "its current on/off state"
            ):
                initial_states = {}
                for tool_key, _ in chat.MODULE_TOGGLE_ORDER:
                    actual_checked = chat.is_module_toggle_checked(tool_key)
                    displayed_checked = chat.is_module_toggle_visually_checked(tool_key)
                    assert displayed_checked == actual_checked, (
                        f"{tool_key} toggle's displayed (visual) state should match "
                        f"its actual checked state — displayed={displayed_checked}, "
                        f"actual={actual_checked}"
                    )
                    initial_states[tool_key] = actual_checked
                logger.info("Modules panel initial toggle states: %s", initial_states)

            with allure.step("Step 7 — Toggle Image creation on then off; verify state + toast each time"):
                initial_checked = chat.is_module_toggle_checked("image_generation")

                chat.click_module_toggle("image_generation", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("image_generation") != initial_checked, (
                    "Image creation toggle state should flip after the first click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

                chat.click_module_toggle("image_generation", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("image_generation") == initial_checked, (
                    "Image creation toggle state should flip back after the second click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 8 — Toggle Data Analysis on; verify state + toast, then restore"):
                initial_checked_da = chat.is_module_toggle_checked("data_analysis")

                chat.click_module_toggle("data_analysis", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("data_analysis") != initial_checked_da, (
                    "Data Analysis toggle state should flip after click"
                )
                expect(chat.toast_message).to_have_text(
                    "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                )

                # Restore original state so this run doesn't leak config forward.
                chat.click_module_toggle("data_analysis", timeout=NETWORK_RESPONSE_TIMEOUT)
                assert chat.is_module_toggle_checked("data_analysis") == initial_checked_da, (
                    "Data Analysis toggle should be restored to its original state"
                )

            with allure.step(
                "Steps 7b/8b (ELITEA-2464 extension) — Toggle every remaining "
                "module one by one; verify state + success toast (no error) "
                "for each, then restore"
            ):
                already_sampled = {"image_generation", "data_analysis"}
                remaining_tool_keys = [
                    tool_key
                    for tool_key, _ in chat.MODULE_TOGGLE_ORDER
                    if tool_key not in already_sampled
                ]
                assert remaining_tool_keys, "Expected at least one un-sampled module toggle"

                for tool_key in remaining_tool_keys:
                    initial = chat.is_module_toggle_checked(tool_key)

                    chat.click_module_toggle(tool_key, timeout=NETWORK_RESPONSE_TIMEOUT)
                    assert chat.is_module_toggle_checked(tool_key) != initial, (
                        f"{tool_key} toggle state should flip after the first click"
                    )
                    expect(chat.toast_message).to_have_text(
                        "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                    )
                    expect(chat.get_toast_alert("success")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                    expect(chat.get_toast_alert("error")).to_have_count(0)

                    chat.click_module_toggle(tool_key, timeout=NETWORK_RESPONSE_TIMEOUT)
                    assert chat.is_module_toggle_checked(tool_key) == initial, (
                        f"{tool_key} toggle should be restored to its original state"
                    )
                    expect(chat.toast_message).to_have_text(
                        "Modules configuration updated", timeout=UI_ELEMENT_TIMEOUT
                    )
                    expect(chat.get_toast_alert("success")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                    expect(chat.get_toast_alert("error")).to_have_count(0)

                    logger.info(
                        "Toggled %s on/off; success toast confirmed, no error toast", tool_key
                    )

            with allure.step("Step 9 — Escape does NOT close the panel; an outside click does"):
                page.keyboard.press("Escape")
                expect(chat.get_module_toggle_switches()).to_have_count(
                    len(chat.MODULE_TOGGLE_ORDER), timeout=UI_ELEMENT_TIMEOUT
                )

                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_module_toggle_switches()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 9b (ELITEA-2464 extension) — Verify the main conversation "
                "view is restored: composer is visible and enabled"
            ):
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        finally:
            with allure.step("Cleanup — delete the generated conversation"):
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Deleted conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)

            with allure.step(
                "Cleanup (ELITEA-2463 extension) — delete the sibling conversation"
            ):
                try:
                    conversation_api.delete_conversation(int(sibling_conv_id))
                    logger.info("Deleted sibling conversation %s", sibling_conv_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup failed for sibling conversation %s: %s", sibling_conv_id, exc
                    )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2163_chat-search-no-results-state.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_search_no_results_state(self, page, conversation_api):
        """Typing a search query that matches nothing shows the search-
        specific "No conversations found" empty state, zero conversation
        rows render, and no console errors/crash occur.

        Runs against the default project (399/"Private"), which already
        carries 45+ unrelated conversations/folders — the correct
        precondition for a genuine "no results" search, as opposed to a
        "this project has never had a conversation" empty state.

        Also carries one soft-asserted, RED-by-design known defect (per
        ``.agents/testing.md`` § Merge gate's sanctioned-RED exception, same
        shape as ``test_attach_unsupported_file_format_error.py``'s
        toast-severity check): GroupedConversations.jsx's "Still no
        conversations created." text incorrectly co-renders alongside the
        correct no-results message on a project that has other, non-matching
        data. The step-4 assertion below asserts the CORRECT expected
        behavior (the misleading text should NOT be visible) via
        ``expect.soft()`` — this is expected to FAIL (RED) until
        EliteaAI/elitea-testing-public#1525 ships; every other assertion in
        this test is a hard assert.
        """
        conv_name = f"AutomationNoResults{uuid4().hex[:8]}"
        no_match_query = "xyznotexists"

        with allure.step("Setup — create a conversation with a unique name via API"):
            conv = conversation_api.create_conversation(conv_name)
            conv_id = str(conv["id"])
            logger.info("Created conversation %s (%s)", conv_id, conv_name)

        try:
            chat = ChatPage(page)
            console_capture = chat.capture_console_errors()

            with allure.step("Step 1 — Navigate to chat; open search"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Type a query with no matches; verify the "
                "search-specific no-results message is shown"
            ):
                chat.type_conversation_search_query(no_match_query, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.search_no_results_message).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Verify no conversation items are displayed"):
                expect(chat.get_conversation_item_rows()).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify no error or crash occurs; page remains stable"):
                assert not console_capture, (
                    f"Unexpected console errors during no-results search: "
                    f"{[m.text for m in console_capture]!r}"
                )
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Known defect: EliteaAI/elitea-testing-public#1525 — the
                # "Still no conversations created." text incorrectly
                # co-renders with the correct no-results message on a
                # project that has other, non-matching data. Asserts the
                # CORRECT expected behavior via expect.soft() — this is
                # RED-by-design (sanctioned RED per .agents/testing.md §
                # Merge gate) until the product fix ships; every other
                # assertion in this test is a hard assert and stays green.
                expect.soft(chat.conversations_empty_state_message).not_to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            console_capture.stop()

        finally:
            with allure.step("Cleanup — delete the generated conversation"):
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Deleted conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2164_chat-search-cleared-by-clicking-x-icon-restores-default-view.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_search_cleared_by_x_icon_restores_default_view(self, page, conversation_api):
        """Clicking the X/clear icon while a search is active fully closes
        the search input (not merely clears its text) and restores the
        default unfiltered conversation list — folders, date groups, and
        the magnifier button all come back."""
        # NOTE: must embed "Un" (case-insensitively) for the "un" partial
        # query to match — plain "Automation..." does NOT contain the
        # substring "un" (live-confirmed: this test originally used
        # "AutomationXClear{hex}" and the "un" query matched nothing).
        conv_name = f"AutomationUniqueXClear{uuid4().hex[:8]}"

        with allure.step("Setup — create a conversation with a unique name via API"):
            conv = conversation_api.create_conversation(conv_name)
            conv_id = str(conv["id"])
            logger.info("Created conversation %s (%s)", conv_id, conv_name)

        try:
            with allure.step(
                "Step 1 — Click magnifier, type 'un', verify filtered results appear"
            ):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                chat.type_conversation_search_query("un", timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Click the X (clear/close) icon"):
                chat.search_conversations_clear_button.click()
                expect(chat.search_conversations_input).not_to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify the left panel returns to the default view "
                "(conversations, folders, date groups)"
            ):
                chat.wait_for_any_folder_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_folder_link_count() > 0, (
                    "Default view should show the project's pre-existing folders "
                    "again after closing search"
                )
                assert chat.is_conversation_in_group(conv_id, group="today", timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_id} should be back inside the 'Today' date "
                    "group after closing search"
                )

            with allure.step("Step 4 — Verify no search filter is applied (all conversations visible)"):
                row_count = chat.get_conversation_item_rows().count()
                assert row_count >= 2, (
                    f"Expected the unfiltered list to show more than just the generated "
                    f"conversation (got {row_count} rows) — a lingering filter would "
                    "still show only 1"
                )

            with allure.step("Step 5 — Verify the magnifier icon is visible again in the CHATS header"):
                expect(chat.search_conversations_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        finally:
            with allure.step("Cleanup — delete the generated conversation"):
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Deleted conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2165_chat-search-input-cleared-by-deleting-text-updates-results-dynamically.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_search_input_cleared_by_deleting_text_updates_dynamically(self, page, conversation_api):
        """Deleting characters from the search query dynamically re-filters
        the list via the same debounced server-driven mechanism as typing —
        narrowing to a longer value shows 1 match, deleting back down to a
        shared prefix grows the match set, and clearing to empty restores
        the full default view (not a distinct empty-search placeholder)."""
        conv_narrow_name = f"AutomationDynUnique{uuid4().hex[:8]}"
        conv_broad_name = f"AutomationDynOther{uuid4().hex[:8]}"
        shared_prefix = "AutomationDyn"

        with allure.step("Setup — create two conversations sharing a common prefix via API"):
            conv_narrow = conversation_api.create_conversation(conv_narrow_name)
            conv_narrow_id = str(conv_narrow["id"])
            conv_broad = conversation_api.create_conversation(conv_broad_name)
            conv_broad_id = str(conv_broad["id"])
            logger.info(
                "Created conversations %s (%s) and %s (%s)",
                conv_narrow_id, conv_narrow_name, conv_broad_id, conv_broad_name,
            )

        try:
            with allure.step(
                "Step 1 — Click magnifier, type the full narrow name; "
                "verify exactly one filtered result"
            ):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                chat.type_conversation_search_query(conv_narrow_name, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item_rows()).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_narrow_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Delete characters down to the shared prefix; "
                "verify results grow to include both conversations"
            ):
                chat.type_conversation_search_query(shared_prefix, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item_rows()).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_narrow_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_broad_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Delete all remaining characters; verify the full "
                "default view is restored with no error"
            ):
                console_capture = chat.capture_console_errors()
                chat.search_conversations_input.click(click_count=3)
                page.keyboard.press("Meta+a")
                page.keyboard.press("Backspace")
                # NOTE: no page.expect_response() wait here — live-confirmed
                # (via a failing first attempt) that clearing the query back
                # to the SAME empty/no-query state the page loaded with can
                # be served entirely from the query-client cache, with no new
                # network round-trip at all. The polling assertions below
                # (is_conversation_in_group, wait_for-backed) are the real
                # settle-wait; a network response is not a reliable signal
                # for this specific transition.
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_group(
                    conv_narrow_id, group="today", timeout=UI_ELEMENT_TIMEOUT
                ), f"Conversation {conv_narrow_id} should be visible in its date group"
                assert chat.is_conversation_in_group(
                    conv_broad_id, group="today", timeout=UI_ELEMENT_TIMEOUT
                ), f"Conversation {conv_broad_id} should be visible in its date group"
                chat.wait_for_any_folder_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_folder_link_count() > 0, (
                    "Default view should show the project's pre-existing folders "
                    "again once the query is fully cleared"
                )
                assert not console_capture, (
                    f"Unexpected console errors while clearing the search query: "
                    f"{[m.text for m in console_capture]!r}"
                )
                console_capture.stop()

        finally:
            with allure.step("Cleanup — delete the generated conversations"):
                for cid in (conv_narrow_id, conv_broad_id):
                    try:
                        conversation_api.delete_conversation(int(cid))
                        logger.info("Deleted conversation %s", cid)
                    except Exception as exc:
                        logger.warning("Cleanup failed for conversation %s: %s", cid, exc)
