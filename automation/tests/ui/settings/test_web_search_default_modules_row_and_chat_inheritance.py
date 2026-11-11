"""UI test — ELITEA-4655: Web Search Default Modules row and Chats-default inheritance.

Settings → General → Default Modules → Web Search row (description + independent
Chats/Agents switches); turning the Chats default ON makes a NEW chat open with
the Web Search module ON, and a prompt really triggers the web_search tool.

The Chats default is persisted per user/project: the test normalises it to OFF
first and restores OFF in ``finally``.

Usage:
    cd automation
    pytest tests/ui/settings/test_web_search_default_modules_row_and_chat_inheritance.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage
from pages.project_general_settings_page import ProjectGeneralSettingsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p1, pytest.mark.chat]

_PROMPT = "search me some todays sport news article"
_DESCRIPTION = "Allow the LLM to search the Internet, read web pages, and cite its sources."
_RESPONSE_TIMEOUT = 120_000


@allure.epic("Settings")
@allure.feature("Default Modules")
class TestWebSearchDefaultModules:
    """ELITEA-4655 — Web Search default-module row and new-chat inheritance."""

    @pytest.mark.tms("ELITEA-4655")
    @allure.title("Web Search Default Modules row, Chats default inherited by a new chat that web-searches")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/default-modules/"
        "ELITEA-4655_web-search-default-modules-tooltip-and-chat-inheritance-triggers-search.md",
        "onetest-ai Test Case link",
    )
    def test_web_search_default_modules_row_and_chat_inheritance(self, page):
        settings = ProjectGeneralSettingsPage(page)
        chat = ChatPage(page)

        try:
            with allure.step("Step 1 — Open Settings → General and wait for Default Modules"):
                settings.open_default_modules()
                expect(settings.default_modules_section).to_be_visible()

            with allure.step("Step 2 — Web Search row shows its descriptive paragraph"):
                expect(settings.web_search_description).to_be_visible()
                expect(settings.web_search_description).to_have_text(_DESCRIPTION)

            with allure.step("Step 3 — Tooltip text is present (in Default Modules the paragraph is the tooltip; no (i) icon)"):
                assert settings.web_search_description.inner_text().strip(), "Web Search description is empty"

            with allure.step("Step 4 — Two separate Chats / Agents switches with column headers"):
                assert settings.is_default_modules_column_header_visible("Chats")
                assert settings.is_default_modules_column_header_visible("Agents")
                switches = settings.web_search_switches()
                assert len(switches) == 2, f"Expected 2 switches (Chats, Agents), got {len(switches)}"

            with allure.step("Step 5 — Normalise Chats to OFF, turn it ON (autosave on blur) and verify persistence"):
                settings.set_web_search_chats_default(False)
                agents_before = settings.web_search_switches()[1].is_checked()
                settings.set_web_search_chats_default(True)
                page.reload()
                settings.wait_for_default_modules()
                chats_switch, agents_switch = settings.web_search_switches()
                expect(chats_switch).to_be_checked()
                assert agents_switch.is_checked() == agents_before, "Agents switch changed when only Chats was toggled"

            with allure.step("Step 6 — Create a new chat conversation"):
                chat.navigate_to_chat()
                chat.click_create_new_conversation()
                expect(chat.new_conversation_greeting).to_be_visible(timeout=15_000)

            with allure.step("Step 7-8 — Modules panel lists Web Search toggled ON"):
                chat.dismiss_platform_release_banner_if_present()
                chat.plus_menu_button.click()
                chat.internal_tools_menuitem.click()
                switch = chat.get_module_toggle_switch("web_search")
                switch.scroll_into_view_if_needed()
                expect(switch).to_be_checked(timeout=15_000)
                assert chat.is_module_toggle_checked("web_search")
                page.keyboard.press("Escape")

            with allure.step("Step 9 — Send the web-search prompt"):
                initial_count = chat.get_message_count()
                chat.send_message(_PROMPT)

            with allure.step("Step 10 — Wait for the response to complete"):
                # wait_for_ai_response keys on a Copy button aria-label DEV no longer renders; use
                # the answer bubble + content stability instead.
                chat.messages_container.nth(initial_count + 1).wait_for(state="visible", timeout=_RESPONSE_TIMEOUT)
                chat.wait_for_message_content_stable(timeout=_RESPONSE_TIMEOUT)

            with allure.step("Step 11 — A web_search tool-use chip is shown"):
                chip = chat.answer_tool_chip.first
                expect(chip).to_be_visible(timeout=30_000)
                expect(chip).to_contain_text("web_search")
        finally:
            with allure.step("Teardown — restore the Chats default to OFF"):
                try:
                    settings.open_default_modules()
                    settings.set_web_search_chats_default(False)
                except Exception:
                    logger.exception("Failed to restore Web Search Chats default to OFF")
                    raise
