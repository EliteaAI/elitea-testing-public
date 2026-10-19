"""UI Test for ELITEA-3366 — Skill creation from chat with complete information.

With the Skills Builder module enabled, a fully specified creation message
makes the assistant create the skill without a clarifying question, render a
generated-entity chip, open the skill in the Canvas editor from that chip, and
NOT add the skill as a conversation participant.

Case-text drift (CLARIFICATIONS, live product is correct — see AFS):
    - the chip label is the skill's slugified ``name``, not "Skill: <Name>";
    - the Canvas Name is that slug; Description is AI-rephrased (asserted
      non-empty + topical), Instructions are byte-exact.

Markers:
    - ui, chat, p0 (AFS l1 / TMS priority critical), regression

Usage:
    cd automation
    pytest tests/ui/chat/test_skill_creation_from_chat_chip_canvas.py -v
"""

import logging
import re
import uuid

import allure
import pytest

from pages.chat_page import ChatPage
from pages.skill_form_page import SkillFormPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

AI_RESPONSE_TIMEOUT = 90_000
UI_ELEMENT_TIMEOUT = 15_000

_DESCRIPTION = "Summarizes daily standup notes into action items"
_INSTRUCTIONS = (
    "Given raw standup notes, extract blockers, decisions, and action items as a bulleted list."
)
_TOOL_CHIP_TEXT = "Elitea Skills: post_elitea_core_skills"
_PARTICIPANT_SECTIONS = ("agents", "pipelines", "toolkits", "mcp")


def _slug(display_name: str) -> str:
    """Mirror the product's display-name -> ``name`` slug (lowercase, hyphenated)."""
    return re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-")


@allure.epic("Chat")
@allure.feature("Skills Builder")
class TestSkillCreationFromChat:
    """ELITEA-3366 — skill created from chat; chip opens Canvas; not a participant."""

    @pytest.mark.tms("ELITEA-3366")
    @allure.title("Skill creation from chat with complete info creates the skill; chip opens it in Canvas")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/build-skills-project-context/ELITEA-3366_skill-creation-happy-path-with-chip-and-canvas.md",
        "onetest-ai Test Case link",
    )
    def test_skill_created_from_chat_chip_opens_canvas(self, page, conversation_api, skill_api):
        chat = ChatPage(page)
        form = SkillFormPage(page)
        display_name = f"Daily Standup Summarizer {uuid.uuid4().hex[:8]}"
        expected_slug = _slug(display_name)
        message = (
            f"Create a skill called '{display_name}' that summarizes daily standup notes into "
            f"action items. Instructions: {_INSTRUCTIONS}"
        )
        conv_id = None

        try:
            with allure.step("Precondition — fresh conversation with the Skills Builder module enabled"):
                chat.navigate_to_chat()
                chat.dismiss_center_banner_if_present()
                chat.click_create_conversation(timeout=UI_ELEMENT_TIMEOUT)
                chat.open_internal_tools_menu()
                chat.ensure_module_toggle_checked("skill_builder", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_module_toggle_checked("skill_builder"), "Skills Builder toggle should be ON"
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 1 — Send the fully specified request; the Skills tool is invoked, no clarifying question"):
                initial_count = chat.get_message_count()
                chat.send_message(message, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_message_content_stable(timeout=AI_RESPONSE_TIMEOUT)
                chips = chat.answer_model_chip
                chip_texts = [(chips.nth(i).text_content() or "").strip() for i in range(chips.count())]
                tool_chips = chat.answer_tool_chip
                chip_texts += [(tool_chips.nth(i).text_content() or "").strip() for i in range(tool_chips.count())]
                assert any(_TOOL_CHIP_TEXT in t for t in chip_texts), (
                    f"Expected a tool chip {_TOOL_CHIP_TEXT!r} (Skills tool invoked without clarification), "
                    f"got {chip_texts!r}"
                )
                match = re.search(r"/chat/(\d+)", page.url)
                conv_id = int(match.group(1)) if match else None

            with allure.step("Step 2 — The response contains exactly one generated-entity (Skill) chip"):
                labels = chat.get_generated_entity_chip_labels(timeout=UI_ELEMENT_TIMEOUT)
                assert len(labels) == 1, f"Expected exactly one generated-entity chip, got {labels!r}"
                assert labels[0] == expected_slug, (
                    f"Chip label should be the created skill's slugified name {expected_slug!r}, got {labels[0]!r}"
                )

            with allure.step("Step 3 — Click the chip's Open entity button: the Skill editor opens in Canvas"):
                chat.open_generated_entity_chip(timeout=UI_ELEMENT_TIMEOUT)
                form.name_input_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Canvas fields carry the created skill's Name / Description / Instructions"):
                assert form.get_name() == expected_slug, (
                    f"Canvas Name should be {expected_slug!r}, got {form.get_name()!r}"
                )
                description = form.get_description().strip().lower()
                assert description and "standup" in description and "action items" in description, (
                    f"Canvas Description should be non-empty and topical ({_DESCRIPTION!r}), got {description!r}"
                )
                assert form.get_instructions_multiline().strip() == _INSTRUCTIONS, (
                    f"Canvas Instructions should be byte-exact, got {form.get_instructions_multiline()!r}"
                )

            with allure.step("Step 5 — The new Skill is not added as a conversation participant"):
                present = [s for s in _PARTICIPANT_SECTIONS if chat.is_participants_badge_visible(timeout=1000, section=s)]
                assert not present, f"Skill creation must not add any participant, badges present: {present}"
        finally:
            try:
                rows = skill_api.list_skills().get("rows", [])
                for row in rows:
                    if row.get("name") == expected_slug:
                        skill_api.delete_skill(row["id"])
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skill cleanup failed: %s", exc)
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Conversation cleanup failed: %s", exc)
