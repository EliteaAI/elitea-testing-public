"""UI Test for ELITEA-3316 — Skill Builder creates the skill in the current project only.

With Skills Builder enabled, a creation message makes the AI create a Skill without
asking for project/user ids (runtime_context supplies them). The skill must exist
in the active project and in no other project.

Case-text drift (AFS): chip label is the slugified name; tool name varies, so only
the ``Elitea Skills:`` prefix is asserted; project selector text carries an avatar
letter, so the project name is matched by substring.

Usage:
    cd automation
    APP_PREFIX=/app pytest tests/ui/chat/test_skill_builder_runtime_context_current_project.py -v
"""

import logging
import re
import uuid

import allure
import pytest

from api.client import SkillAPI
from pages.chat_page import ChatPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.skills,
    pytest.mark.p0,
    pytest.mark.regression,
]

AI_RESPONSE_TIMEOUT = 120_000
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
TOOL_CALL_PREFIX = "Elitea Skills:"
OTHER_PROJECT_IDS = ("470", "1")  # Elitea Automation, Public
ACTIVE_PROJECT_NAME = "Private"


def _slugify(display_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-")


def _skill_names(api: SkillAPI) -> list[str]:
    return [row.get("name") for row in api.list_skills().get("rows", [])]


@allure.epic("Chat")
@allure.feature("Skills Builder")
class TestSkillBuilderRuntimeContext:
    """ELITEA-3316 — skill created in the current project only."""

    @pytest.mark.tms("ELITEA-3316")
    @allure.title("Skill Builder creates the skill in the current project only")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_skill_created_in_current_project_only(self, page, conversation_api, skill_api):
        chat = ChatPage(page)
        token = uuid.uuid4().hex[:8]
        display_name = f"Meeting Notes Summarizer {token}"
        slug = _slugify(display_name)
        message = f"Create a skill called '{display_name}' that summarizes meeting notes into action items"
        conv_id = None
        cookies = None
        other_apis: list[SkillAPI] = []

        try:
            with allure.step("Step 1 — Confirm the active project (project A)"):
                chat.navigate_to_chat()
                chat.dismiss_platform_banner_dialog()
                project_text = chat.get_selected_project_text()
                assert ACTIVE_PROJECT_NAME in project_text, (
                    f"Expected active project {ACTIVE_PROJECT_NAME!r} in selector, got {project_text!r}"
                )
                cookies = page.context.cookies()
                other_apis = [SkillAPI(cookies, project_id=pid) for pid in OTHER_PROJECT_IDS]
                assert slug not in _skill_names(skill_api), "Precondition: slug must not pre-exist in project A"

            with allure.step("Step 2 — Enable Skills Builder via the Modules toggle"):
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                chat.dismiss_platform_banner_dialog()
                conv_id = chat.get_current_conversation_id()
                chat.open_internal_tools_menu()
                chat.ensure_module_toggle_checked("skill_builder", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_module_toggle_checked("skill_builder"), "Skills Builder toggle should be on"
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 3 — Send the creation message; AI proceeds without project/user questions"):
                initial_count = chat.get_message_count()
                chat.send_message(message, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
                evidence = chat.get_tool_chip_and_message_text()
                assert TOOL_CALL_PREFIX in evidence, (
                    f"Expected a Skills tool call chip ('{TOOL_CALL_PREFIX} ...'), got: {evidence[:500]!r}"
                )
                if conv_id is None:
                    conv_id = chat.get_current_conversation_id()

            with allure.step("Step 4 — Response contains exactly one Skill chip labelled with the skill name"):
                labels = chat.get_generated_entity_chip_labels()
                assert len(labels) == 1, f"Expected exactly one generated-entity chip, got {labels}"
                assert labels[0] == slug, f"Chip label should be {slug!r}, got {labels[0]!r}"

            with allure.step("Step 5 — Project A skills list contains the new skill"):
                assert slug in _skill_names(skill_api), f"Skill {slug!r} missing from the current project's list"

            with allure.step("Step 6 — Other projects' skills lists do NOT contain the skill"):
                for pid, api in zip(OTHER_PROJECT_IDS, other_apis):
                    assert slug not in _skill_names(api), f"Skill {slug!r} leaked into project {pid}"
        finally:
            with allure.step("Cleanup — delete created skill and conversation"):
                for api in [skill_api, *other_apis]:
                    try:
                        for row in api.list_skills().get("rows", []):
                            if row.get("name") == slug:
                                api.delete_skill(row["id"])
                                logger.info("Deleted skill %s in project %s", row["id"], api.project_id)
                    except Exception as exc:
                        logger.warning("Skill cleanup failed: %s", exc)
                if conv_id:
                    try:
                        conversation_api.delete_conversation(conv_id)
                    except Exception as exc:
                        logger.warning("Conversation cleanup failed: %s", exc)
