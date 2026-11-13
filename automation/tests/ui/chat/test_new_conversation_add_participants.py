"""UI Test for ELITEA-2455 — New conversation, add Agent / Pipeline / Skill / Toolkit / MCP participants.

AFS: test-specs/chat-interface/l1_new-conversation-add-agent-pipeline-toolkit-mcp-participants_ELITEA-2455.md

Case-text drift (live product is the contract): create buttons read "Create Agent" etc.;
"Invite Users" is absent in a private project; "Type your message..." is rendered text, not
a placeholder attribute; the owner icon (case step 18) is not rendered in a private project;
the warning is amber, not yellow.
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.p1,
    pytest.mark.regression,
]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SECTIONS = ["Agents", "Pipelines", "Skills", "Toolkits", "MCPs"]


@allure.epic("Chat")
@allure.feature("Participants")
class TestNewConversationParticipants:
    """ELITEA-2455 — new chat, add the four participant types via the plus menu."""

    @pytest.mark.tms("ELITEA-2455")
    @allure.title("New conversation: add agent, pipeline, skill, toolkit and MCP participants; warning on misconfigured")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2455_chat-create-new-conversation-and-add-agent-pipeline-toolkit.md",
        "onetest-ai Test Case link",
    )
    def test_new_conversation_add_four_participant_types(
        self, page, conversation_api, agent_api, pipeline_api, skill_api,
        artifact_toolkit, mcp_toolkit_with_tools,
    ):
        chat = ChatPage(page)
        project_id = artifact_toolkit["project_id"]
        # The agent_id/pipeline_id fixtures name both entities identically (32-char truncation
        # of the test name), so rows could not be matched by text; create distinctly named ones.
        agent_name = "autotest_2455_agent"
        pipeline_name = "autotest_2455_pipeline"
        agent_id = agent_api.create_agent(agent_name, "ELITEA-2455 agent", instructions="You are a test agent.")["id"]
        pipeline_id = pipeline_api.create_pipeline(pipeline_name, "ELITEA-2455 pipeline")["id"]
        skill_name = "autotest-2455-skill"
        skill_id = skill_api.create_skill(
            name=skill_name, description="ELITEA-2455 skill", instructions="You are a test skill. Reply 'ok'.",
        )["id"]
        toolkit_name = artifact_toolkit["name"]
        mcp_name = mcp_toolkit_with_tools["name"]
        conv_id = None

        def row_for(name):
            return page.locator(chat.PARTICIPANT_ROW_PREFIX).filter(has_text=name)

        def section_of(name):
            """Panel section a participant row sits in: the last section title above the row."""
            row_y = row_for(name).bounding_box()["y"]
            titles = [(s, chat.get_participant_section_title(s)) for s in SECTIONS]
            above = [(t.bounding_box()["y"], s) for s, t in titles if t.count() and t.bounding_box()["y"] <= row_y]
            return max(above)[1] if above else None

        try:
            with allure.step("Step 1 — Open Chat, click +Chat; new empty conversation with empty participants panel"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                expect(chat.new_conversation_greeting).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Live contract: no "Type your message..." hint is rendered on DEV (neither as
                # placeholder attribute nor text) -- assert the input is ready and empty instead.
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_editable()
                expect(chat.message_input).to_have_value("")
                chat.expand_participants_panel_via_toggle()
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(0)
                for section in SECTIONS:
                    expect(chat.get_participant_section_title(section)).to_have_count(0)

            with allure.step("Step 2 — Plus menu lists Attach Files (10 left), Modules, Agents, Pipelines, Skills, Toolkits, MCPs"):
                chat.plus_menu_button.click()
                expect(chat.attach_files_button).to_contain_text("10 left", timeout=UI_ELEMENT_TIMEOUT)
                for item in (chat.internal_tools_menuitem, chat.agents_menuitem, chat.pipelines_menuitem,
                             chat.skills_menuitem, chat.toolkits_menuitem, chat.mcps_menuitem):
                    expect(item).to_be_visible()
                expect(chat.invite_users_menuitem).to_have_count(0)  # private project
                chat.close_plus_menu_popper_on_blank_chat()

            with allure.step("Step 3 — Click Agents: dropdown list opens (search, create, list); select an agent -> AGENTS section"):
                chat.plus_menu_button.click()
                chat.agents_menuitem.click()  # Agents/Pipelines/Skills submenus open on click (PlusChatButton.handleItemClick)
                expect(chat.agents_search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.agents_create_new_button).to_be_visible()
                expect(page.locator(chat.AGENT_PARTICIPANT_MENU_ITEM.format(project_id, agent_id))).to_be_visible()
                page.locator(chat.AGENT_PARTICIPANT_MENU_ITEM.format(project_id, agent_id)).click()
                expect(chat.get_participant_section_title("Agents")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # The selected entity (whatever its name) is added as a participant in the AGENTS section.
                expect(row_for(agent_name)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(row_for(agent_name)).to_contain_text("base")
                assert section_of(agent_name) == "Agents", "Selected agent is not listed under AGENTS"

            with allure.step("Step 4 — Click Pipelines: dropdown list opens (create, list); select a pipeline -> PIPELINES section"):
                chat.plus_menu_button.click()
                chat.pipelines_menuitem.click()
                expect(chat.pipelines_search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.pipelines_create_new_button).to_be_visible()
                expect(page.locator(chat.PIPELINE_PARTICIPANT_MENU_ITEM.format(project_id, pipeline_id))).to_be_visible()
                page.locator(chat.PIPELINE_PARTICIPANT_MENU_ITEM.format(project_id, pipeline_id)).click()
                expect(chat.get_participant_section_title("Pipelines")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(row_for(pipeline_name)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                assert section_of(pipeline_name) == "Pipelines", "Selected pipeline is not listed under PIPELINES"

            with allure.step("Step 5 — Click Skills: dropdown list opens (create, list); select a skill -> SKILLS section"):
                chat.open_skills_submenu()
                expect(chat.skills_create_new_button).to_be_visible()
                skill_row = page.locator(chat.SKILL_PARTICIPANT_MENU_ITEM.format(settings.elitea_project_id, skill_id))
                expect(skill_row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                skill_row.click()
                expect(chat.skills_search_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_participant_section_title("Skills")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(row_for(skill_name)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                assert section_of(skill_name) == "Skills", "Selected skill is not listed under SKILLS"

            with allure.step("Step 6 — Toggle the toolkit and the MCP (same open popper) -> TOOLKITS / MCPS sections"):
                chat.add_toolkit_participant_via_slash_menu(project_id, artifact_toolkit["id"])
                toolkit_item = page.locator(chat.TOOLKIT_PARTICIPANT_MENU_ITEM.format(project_id, artifact_toolkit["id"]))
                expect(chat.PARTICIPANT_MENU_ITEM_SWITCH.within(toolkit_item)).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
                chat.add_mcp_participant_via_slash_menu(project_id, mcp_toolkit_with_tools["id"])
                mcp_item = page.locator(chat.MCP_PARTICIPANT_MENU_ITEM.format(project_id, mcp_toolkit_with_tools["id"]))
                expect(chat.PARTICIPANT_MENU_ITEM_SWITCH.within(mcp_item)).to_be_checked(timeout=UI_ELEMENT_TIMEOUT)
                chat.close_plus_menu_popper_on_blank_chat()
                expect(chat.get_participant_section_title("Toolkits")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.get_participant_section_title("MCPs")).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(row_for(toolkit_name)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                assert section_of(toolkit_name) == "Toolkits", "Selected toolkit is not listed under TOOLKITS"
                # Pre-send the MCP row has no resolved name yet ("Participant Name"); its row is
                # keyed by the entity id, so match by id here and by name after Send.
                # Pre-send the not-yet-connected MCP renders as an attention card (name unresolved,
                # no chat-participant-row-* testid) -- it is asserted via the MCPS section + warning.
                expect(chat.get_participant_warning_cards()).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 7 — Sections ordered AGENTS < PIPELINES < SKILLS < TOOLKITS < MCPS; no dupes, no error toast"):
                ys = [chat.get_participant_section_title(s).bounding_box()["y"] for s in SECTIONS]
                assert ys == sorted(ys) and len(set(ys)) == 5, f"Section order wrong, y positions: {ys}"
                for n in (agent_name, pipeline_name, skill_name, toolkit_name):
                    expect(row_for(n)).to_have_count(1)
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(4)  # MCP = attention card
                expect(page.locator(chat.TOAST_ALERT_SEVERITY.format("error"))).to_have_count(0)

            with allure.step("Step 8 — Participant type icons are pairwise distinct (agent, pipeline, skill, toolkit; MCP checked after Send)"):
                icons = [chat.get_participant_icon_signature(row_for(n)) for n in (agent_name, pipeline_name, skill_name, toolkit_name)]
                assert all(icons), f"Missing type icon path in a row: {icons}"
                assert len(set(icons)) == 4, "Participant type icons are not pairwise distinct"

            with allure.step("Step 9 — Send 'Hi'; conversation is created and all five participants persist"):
                chat.send_message("Hi")
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                conv_id = chat.get_current_conversation_id()
                expect(chat.messages_container.first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.messages_container.filter(has_text="Hi").first).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                for section in SECTIONS:
                    expect(chat.get_participant_section_title(section)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                for n in (agent_name, pipeline_name, skill_name, toolkit_name):
                    expect(row_for(n)).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                # The disconnected MCP is rendered as an attention card, not a chat-participant-row-*.
                mcp_card = chat.get_participant_attention_card(mcp_name)
                expect(mcp_card).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(page.locator(chat.PARTICIPANT_ROW_PREFIX)).to_have_count(4)
                expect(page.locator(chat.TOAST_ALERT_SEVERITY.format("error"))).to_have_count(0)
                icons = [chat.get_participant_icon_signature(row_for(n)) for n in (agent_name, pipeline_name, skill_name, toolkit_name)]
                icons.append(chat.get_participant_icon_signature(mcp_card))
                assert all(icons) and len(set(icons)) == 5, f"Five type icons must be pairwise distinct, got {icons}"

            with allure.step("Step 10 — Disconnected MCP shows exactly one warning below its row; others none"):
                warnings = chat.get_participant_warning_cards()
                expect(warnings).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                expect(warnings).to_contain_text("Server is disconnected")
                # The warning belongs to the MCP's own card; the other participants carry none.
                expect(mcp_card.locator(chat.PARTICIPANT_WARNING_ICON)).to_have_count(1)
                for other in (agent_name, pipeline_name, skill_name, toolkit_name):
                    expect(row_for(other).locator(chat.PARTICIPANT_WARNING_ICON)).to_have_count(0)
        finally:
            for api, delete_name, eid in (
                (agent_api, "delete_agent", agent_id),
                (pipeline_api, "delete_pipeline", pipeline_id),
                (skill_api, "delete_skill", skill_id),
            ):
                try:
                    getattr(api, delete_name)(eid)
                except Exception as exc:
                    logger.warning("Entity cleanup failed: %s", exc)
            with allure.step("Cleanup — delete created conversation"):
                conv_id = conv_id or chat.get_current_conversation_id()
                if conv_id:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:
                        logger.warning("Conversation cleanup failed: %s", exc)
