"""UI Test for ELITEA-2455 — Chat: create a new conversation and add Agent,
Pipeline, Toolkit and MCP as participants.

Spec: test-specs/chat-interface/l1_chat-create-conversation-add-agent-pipeline-toolkit-mcp-participants_ELITEA-2455.md

Entities are fixture-generated (the case's literal names are cosmetic). The
MCP fixture points at a Remote MCP that DEV reports as disconnected, which is
exactly the "misconfigured entity" the case's final step expects to be flagged.
Step 18 (owner icon in PARTICIPANTS) is not observable in a Private project --
see the AFS Coverage Map.
"""

import logging
import re

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

UI_TIMEOUT = 10_000
SECTION_LABELS = ["Agents", "Pipelines", "Toolkits", "MCPs"]


class TestChatAddParticipants:
    """ELITEA-2455: Chat – add Agent, Pipeline, Toolkit, MCP as participants (critical)."""

    @pytest.mark.tms("ELITEA-2455")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2455_chat-create-new-conversation-and-add-agent-pipeline-toolkit.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p0
    def test_create_conversation_and_add_all_participant_types(
        self, page, conversation_api, agent_id, pipeline_id, artifact_toolkit, mcp_toolkit_with_tools,
    ):
        chat = ChatPage(page)
        project_id = mcp_toolkit_with_tools["project_id"]
        created_conversation_id = None

        try:
            with allure.step("Step 1 — Open Chats and click + Chat; new blank conversation with composer placeholder"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_new_conversation()
                expect(chat.message_input).to_be_visible(timeout=UI_TIMEOUT)
                expect(chat.message_input).to_have_attribute("placeholder", "Type your message...", timeout=UI_TIMEOUT)

            with allure.step("Step 2 — PARTICIPANTS panel is visible and has no participants yet"):
                chat.dismiss_platform_announcement()
                chat.expand_participants_panel_via_toggle()
                expect(chat.get_participant_rows()).to_have_count(0, timeout=UI_TIMEOUT)
                for label in SECTION_LABELS:
                    expect(chat.get_participant_section_title(label)).to_have_count(0)

            with allure.step("Step 3 — Plus menu lists Modules, Agents, Pipelines, Toolkits, MCPs"):
                chat.plus_menu_button.click()
                for tid in ("internal-tools", "agents", "pipelines", "toolkits", "mcps"):
                    expect(page.get_by_test_id(f"{tid}-menuitem")).to_be_visible(timeout=UI_TIMEOUT)
                expect(chat.attach_files_button).to_be_visible(timeout=UI_TIMEOUT)
                chat.close_plus_menu_popper_in_blank_conversation()

            with allure.step("Step 4 — Agents submenu (search, Create, list) and add the agent"):
                chat.open_plus_menu_submenu("agents")
                expect(chat.agents_search_input).to_be_visible()
                expect(chat.agents_create_new_button).to_be_visible()
                agent_row = chat.get_participant_menu_item("agent", project_id, agent_id)
                expect(agent_row).to_be_visible(timeout=UI_TIMEOUT)
                agent_row.click()
                chat.wait_for_network()
                chat.close_plus_menu_popper_in_blank_conversation()
                expect(chat.get_participant_section_title("Agents")).to_be_visible(timeout=UI_TIMEOUT)
                agent_panel_row = chat.get_participant_row_by_entity_id(agent_id)
                expect(agent_panel_row).to_be_visible(timeout=UI_TIMEOUT)
                expect(agent_panel_row).to_contain_text("autotest_")
                expect(agent_panel_row).to_contain_text("base")  # version

            with allure.step("Step 5 — Pipelines submenu (search, Create, list) and add the pipeline"):
                chat.open_plus_menu_submenu("pipelines")
                expect(chat.pipelines_search_input).to_be_visible()
                expect(chat.pipelines_create_new_button).to_be_visible()
                pipeline_row = chat.get_participant_menu_item("pipeline", project_id, pipeline_id)
                expect(pipeline_row).to_be_visible(timeout=UI_TIMEOUT)
                pipeline_row.click()
                chat.wait_for_network()
                chat.close_plus_menu_popper_in_blank_conversation()
                expect(chat.get_participant_section_title("Pipelines")).to_be_visible(timeout=UI_TIMEOUT)
                pipeline_panel_row = chat.get_participant_row_by_entity_id(pipeline_id)
                expect(pipeline_panel_row).to_be_visible(timeout=UI_TIMEOUT)

            with allure.step("Step 6 — Toolkits submenu (toggle rows) and enable the toolkit"):
                chat.open_plus_menu_submenu("toolkits")
                expect(chat.toolkits_create_new_button).to_be_visible()
                toolkit_row = chat.get_participant_menu_item("toolkit", project_id, artifact_toolkit["id"])
                expect(toolkit_row).to_be_visible(timeout=UI_TIMEOUT)
                toolkit_row.click()
                chat.wait_for_network()
                chat.close_plus_menu_popper_in_blank_conversation()
                expect(chat.get_participant_section_title("Toolkits")).to_be_visible(timeout=UI_TIMEOUT)
                toolkit_panel_row = chat.get_participant_row_by_entity_id(artifact_toolkit["id"])
                expect(toolkit_panel_row).to_be_visible(timeout=UI_TIMEOUT)
                expect(toolkit_panel_row).to_contain_text(artifact_toolkit["name"][:15])

            with allure.step("Step 7 — MCPs submenu (toggle rows) and enable the MCP"):
                chat.open_plus_menu_submenu("mcps")
                expect(chat.mcps_create_new_button).to_be_visible()
                mcp_row = chat.get_participant_menu_item("mcp", project_id, mcp_toolkit_with_tools["id"])
                expect(mcp_row).to_be_visible(timeout=UI_TIMEOUT)
                mcp_row.click()
                chat.wait_for_network()
                chat.close_plus_menu_popper_in_blank_conversation()
                expect(chat.get_participant_section_title("MCPs")).to_be_visible(timeout=UI_TIMEOUT)
                expect(chat.get_participant_name_text(mcp_toolkit_with_tools["name"][:15]).first).to_be_visible(
                    timeout=UI_TIMEOUT,
                )

            with allure.step("Step 8 — Sections appear in order AGENTS, PIPELINES, TOOLKITS, MCPS"):
                ys = [chat.get_participant_section_title(label).bounding_box()["y"] for label in SECTION_LABELS]
                assert ys == sorted(ys) and len(set(ys)) == 4, f"Section order wrong, y-coords: {ys}"

            with allure.step("Step 9 — Agent, pipeline and toolkit rows each show a distinct icon"):
                icons = {
                    kind: chat.get_participant_row_icon_geometry(row)
                    for kind, row in (
                        ("agent", agent_panel_row), ("pipeline", pipeline_panel_row), ("toolkit", toolkit_panel_row),
                    )
                }
                assert all(icons.values()), f"Missing icon geometry: {icons}"
                assert len(set(icons.values())) == 3, "Agent/Pipeline/Toolkit icons are not pairwise distinct"
                expect(chat.get_participant_section_title("MCPs")).to_be_visible()

            with allure.step("Step 10 — No duplicate entries and no error messages"):
                rows = chat.get_participant_rows()
                expect(rows).to_have_count(3)
                testids = [rows.nth(i).get_attribute("data-testid") for i in range(rows.count())]
                assert len(set(testids)) == len(testids), f"Duplicate participant rows: {testids}"
                for label in SECTION_LABELS:
                    expect(chat.get_participant_section_title(label)).to_have_count(1)
                expect(chat.get_participant_name_text(mcp_toolkit_with_tools["name"][:15])).to_have_count(1)

            with allure.step("Step 11 — Send 'Hi'; the conversation is created"):
                chat.message_input.click()
                chat.message_input.press_sequentially("Hi")
                chat.send_button.click()
                page.wait_for_url(re.compile(r"/chat/\d+"), timeout=30_000)
                created_conversation_id = int(re.search(r"/chat/(\d+)", page.url).group(1))
                logger.info("Conversation created: %s", created_conversation_id)

            with allure.step("Step 12 — All added participants remain under their type sections"):
                for label in SECTION_LABELS:
                    expect(chat.get_participant_section_title(label)).to_be_visible(timeout=UI_TIMEOUT)
                # Row testids switch from entity ids to persisted participant ids on
                # send, so identify rows by their visible names, not by id.
                rows_after = chat.get_participant_rows()
                expect(rows_after).to_have_count(3, timeout=UI_TIMEOUT)
                expect(rows_after.filter(has_text=artifact_toolkit["name"][:15])).to_have_count(1)
                expect(chat.get_participant_name_text(mcp_toolkit_with_tools["name"][:15])).to_have_count(1)

            with allure.step("Step 13 — Misconfigured entity (disconnected MCP) shows the warning indicator"):
                warnings = chat.get_participant_warning_icons()
                expect(warnings).to_have_count(1, timeout=UI_TIMEOUT)
                expect(warnings.first).to_be_visible()
                expect(chat.get_participant_name_text("Server is disconnected").first).to_be_visible()
        finally:
            if created_conversation_id is not None:
                try:
                    conversation_api.delete_conversation(created_conversation_id)
                except Exception as exc:  # cleanup must never mask the verdict
                    logger.warning("Failed to delete conversation %s: %s", created_conversation_id, exc)
