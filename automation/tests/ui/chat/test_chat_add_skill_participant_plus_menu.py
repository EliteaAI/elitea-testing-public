"""UI Test for ELITEA-4628 — Chat: add own + Catalog skill as participants from the "+" menu.

AFS: test-specs/chat-interface/l1_add-skill-participant-from-plus-menu_ELITEA-4628.md

Case-text drift (live product is the contract): example skills jira-skill/code-task-breakdown do
not exist (a fixture skill is created); an own skill's version badge reads "base", the catalog
skill reads "v1.0"; "Invite Users" is absent in a private project; Skills submenu opens on click.
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.skills,
    pytest.mark.p0,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
CATALOG_SKILL = "code-reviewer"
CATALOG_PROJECT_ID = 1


@allure.epic("Chat")
@allure.feature("Participants")
class TestChatAddSkillParticipant:
    """ELITEA-4628 — add an own skill and a Catalog skill as participants via the plus menu."""

    @pytest.mark.tms("ELITEA-4628")
    @allure.title("Chat: add own skill and Catalog skill as participants from the + menu")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4628_add-skill-participant-from-plus-menu.md",
        "onetest-ai Test Case link",
    )
    def test_add_own_and_catalog_skill_participants(self, page, skill_api):
        chat = ChatPage(page)
        own_name = f"autotest-4628-{int(time.time())}"[:32]
        skill_id = None
        try:
            with allure.step("Setup — create own skill via API"):
                skill = skill_api.create_skill(
                    name=own_name,
                    description="Autotest skill for ELITEA-4628.",
                    instructions="You are a test skill. Reply 'ok'.",
                )
                skill_id = skill["id"]

            with allure.step("Step 1 — Open chat, start a blank conversation, expand participants panel"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                expect(chat.new_conversation_greeting).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.expand_participants_panel_via_toggle()
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(0)

            with allure.step("Step 2 — Plus menu lists Attach Files, Modules, Agents, Pipelines, Skills, Toolkits, MCPs"):
                chat.plus_menu_button.click()
                expect(chat.attach_files_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                for item in (chat.internal_tools_menuitem, chat.agents_menuitem, chat.pipelines_menuitem,
                             chat.skills_menuitem, chat.toolkits_menuitem, chat.mcps_menuitem):
                    expect(item).to_be_visible()
                expect(chat.skills_menuitem).to_contain_text("Skills")
                expect(chat.invite_users_menuitem).to_have_count(0)  # private project
                chat.close_plus_menu_popper_on_blank_chat()

            with allure.step("Step 3 — Skills submenu opens with search field and Create Skill"):
                chat.open_skills_submenu()
                expect(chat.skills_search_input).to_have_attribute("placeholder", "Search skills...")
                expect(chat.skills_create_new_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — List contains the own skill and the catalog skill"):
                chat.skills_search_input.fill(own_name)
                own_row = page.locator(chat.SKILL_PARTICIPANT_MENU_ITEM.format(settings.elitea_project_id, skill_id))
                expect(own_row).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                chat.skills_search_input.fill(CATALOG_SKILL)
                catalog_row = chat.get_skill_menu_item_by_name(CATALOG_SKILL)
                expect(catalog_row).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                assert f"skill-{CATALOG_PROJECT_ID}-" in catalog_row.get_attribute("data-testid")

            with allure.step("Step 5 — Catalog row shows 'Catalog'; own row does not"):
                expect(catalog_row).to_contain_text("Catalog")
                chat.skills_search_input.fill(own_name)
                expect(own_row).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(own_row).not_to_contain_text("Catalog")

            with allure.step("Step 6 — Select the own skill; popper closes; SKILLS section shows name + version"):
                own_row.click()
                expect(chat.skills_search_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_participant_section_title("Skills")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                own_participant = page.locator(chat.PARTICIPANT_ROW_PREFIX).filter(has_text=own_name)
                expect(own_participant).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(own_participant).to_contain_text("base")
                expect(own_participant.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_count(0)

            with allure.step("Step 7 — Re-open Skills and select the catalog skill; popper closes"):
                chat.add_skill_participant(CATALOG_SKILL)

            with allure.step("Step 8 — SKILLS section holds both rows under one header; catalog row has tag + v1.0"):
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_participant_section_title("Skills")).to_have_count(1)
                catalog_participant = page.locator(chat.PARTICIPANT_ROW_PREFIX).filter(has_text=CATALOG_SKILL)
                expect(catalog_participant).to_have_count(1)
                expect(catalog_participant.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_text("Catalog")
                expect(catalog_participant).to_contain_text("v1.0")
                expect(own_participant).to_have_count(1)
                expect(own_participant.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_count(0)
        finally:
            if skill_id:
                with allure.step("Cleanup — delete own skill"):
                    try:
                        skill_api.delete_skill(skill_id)
                    except Exception as exc:
                        logger.warning("Skill cleanup failed: %s", exc)
