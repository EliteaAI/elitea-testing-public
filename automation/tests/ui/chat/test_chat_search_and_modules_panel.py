"""UI Tests for Chat search filters and Modules panel toggles (ELITEA-2162,
extended by ELITEA-2464).

Verifies the search icon opens a search field, partial and full-name queries
filter the conversation list, clicking a result opens the conversation, and
the Modules panel (+ -> Modules, hover) shows 8 toggleable modules that
persist via a confirmation toast — and that only an outside click (not
Escape) closes the panel. ELITEA-2464 extends this with: the full plus-menu
popup (6 top-level options), every module toggle exercised (not just 2
sampled), an explicit no-error-toast check, and a main-conversation-view-
restored check after closing the panel.

Markers:
    - ui: requires browser
    - p1: high priority (case priority "high" -> p1 pytest marker convention)
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

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

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
    @pytest.mark.p1
    def test_search_filters_and_modules_panel_toggles(self, page, conversation_api):
        """Search icon filters conversations by partial/exact query, opens a
        result, and the Modules panel's toggles persist with a confirmation
        toast; closing works via outside click only (not Escape).

        ELITEA-2464 extension: full plus-menu popup verified before opening
        Modules, every module toggle exercised (not just 2 sampled), an
        explicit no-error-toast check per toggle, and the main conversation
        view (composer) verified restored after closing the panel."""
        conv_name = f"AutomationUnique{uuid4().hex[:8]}"

        with allure.step("Setup — create a conversation with a unique name via API"):
            conv = conversation_api.create_conversation(conv_name)
            conv_id = str(conv["id"])
            logger.info("Created conversation %s (%s)", conv_id, conv_name)

        try:
            with allure.step("Step 1 — Navigate to chat; verify search icon visible"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                expect(chat.search_conversations_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 2 — Click search icon; verify input focused + clear icon visible"):
                chat.open_search_conversations_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_input).to_be_focused(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.search_conversations_clear_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Type partial query 'un'; verify the generated conversation appears"):
                chat.type_conversation_search_query("un", timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Type the exact full-name query; verify exactly one matching row"):
                chat.type_conversation_search_query(conv_name, timeout=NETWORK_RESPONSE_TIMEOUT)
                expect(chat.get_conversation_item_rows()).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_conversation_item(conv_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

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

            with allure.step("Step 6 — Hover Modules menuitem to open Modules panel; verify 8 toggles in order"):
                chat.internal_tools_menuitem.hover()
                chat.verify_module_toggle_order(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 6b (ELITEA-2464 extension) — Verify each toggle displays "
                "its current on/off state"
            ):
                initial_states = {
                    tool_key: chat.is_module_toggle_checked(tool_key)
                    for tool_key, _ in chat.MODULE_TOGGLE_ORDER
                }
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
