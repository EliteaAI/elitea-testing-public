"""Interact with Skills from Conversation (ELITEA-1736).

Verifies that a skill attached to an agent can be invoked selectively via the
"~<skill-name>" mention syntax when the agent is added as a **chat
participant** (a different code path from ELITEA-1735's agent-level embedded
chat), and that a plain message (no mention) does not apply the attached
skill's formatting.

Spec: test-specs/skills/l3_interact-with-skills-from-conversation_ELITEA-1736.md
"""

import logging
import re

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.chat_page import ChatPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.chat]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

logger = logging.getLogger("elitea.tests.skills")

SKILL_NAME = "elitea-1736-uppercase-skill"
SKILL_INSTRUCTIONS = (
    "Always respond with the exact text the user asked for, but convert the "
    "ENTIRE output to UPPER CASE letters. Do not use any lowercase letters "
    "in your response."
)
AGENT_NAME = "elitea-1736-conversation-agent"

# Plain question for Step 5 - agent should answer normally without applying skills
PLAIN_QUESTION = "Hello, how are you today?"

# Neutral text for skill mention test (Step 6)
# Skill will transform this text literally according to its instructions
NEUTRAL_TEXT_FOR_SKILL = "The quick brown fox jumps over the lazy dog"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow used in test_skill_agent_interaction.py
    (ELITEA-1735): fill the form (name / description / CodeMirror
    instructions), save, and confirm navigation to the detail page.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=f"ELITEA-1736 automation skill — {name}",
    )
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for skill '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", name, skill_id)
    return skill_id


def _extract_conversation_id(page) -> str | None:
    """Extract the conversation ID from the current URL (``/chat/{id}``)."""
    match = re.search(r"/chat/(\d+)", page.url)
    if match:
        return match.group(1)
    return None


class TestInteractWithSkillsFromConversation:
    """Interact with Skills from Conversation (ELITEA-1736, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1736_interact-with-skills-from-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_interact_with_skills_from_conversation(
        self, page, agent_api, skill_api, conversation_api,
    ):
        """Create a skill, attach it to an agent, add the agent as a chat
        participant, and verify selective invocation via "~<skill-name> <prompt>".

        Steps (AFS test-specs/skills/l3_interact-with-skills-from-conversation_ELITEA-1736.md):
        1. Create Skill (uppercase-formatting instructions).
        2. Create an Agent.
        3. Attach the skill to the agent via the Skills section.
        4. Open Chat, add the agent as a participant.
        5. Send a plain message (no mention) — should NOT apply skill formatting.
        6. Send "~<skill-name> <prompt>" — should return entirely UPPER CASE.
        """
        skill_id = None
        agent_id = None
        conversation_id = None
        # Soft failures list — record failures here instead of raising immediately,
        # so step 6 still executes and reports. If anything landed here, the test
        # fails at the very end via pytest.fail().
        soft_failures = []

        try:
            with allure.step("Step 1 — Create Skill (uppercase-formatting instructions)"):
                skill_id = _create_skill(page, SKILL_NAME, SKILL_INSTRUCTIONS)

            with allure.step("Step 2 — Create Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description="General purpose test assistant for automation",
                    instructions="You are a helpful assistant. Answer questions naturally and conversationally.",
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", AGENT_NAME, agent_id)

            with allure.step("Step 3 — Attach the skill to the agent"):
                detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should render after attaching"
                )

            with allure.step("Step 4 — Open Chat and add the Agent as a participant"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_add_agent_button(NAVIGATION_TIMEOUT)
                chat.add_agent_participant(AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)

                assert chat.is_agent_participant_in_composer(
                    AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"Model Selector composer should show '{AGENT_NAME}' as the "
                    "active agent participant after adding it"
                )

            with allure.step(
                "Step 5 — Plain message (no mention) should NOT apply skill formatting"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(PLAIN_QUESTION, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                chat.wait_for_message_content_stable(
                    stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT,
                )
                # The first message navigates the SPA to /chat/{id}?name=... and
                # re-renders the composer, which is briefly disabled during that
                # transition — wait for it to become interactable again (visible
                # AND editable, not just visible) before sending the mention
                # message in step 6.
                chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

                conversation_id = _extract_conversation_id(page)
                assert conversation_id, (
                    "Sending the first message should create a conversation and "
                    f"update the URL to /chat/{{id}} — got {page.url!r}"
                )

                plain_response = chat.get_last_message_text()
                logger.info("Plain response (no mention): %r", plain_response)
                alpha_chars = [c for c in plain_response if c.isalpha()]

                # Without ~mention, agent should NOT apply skill formatting
                is_all_uppercase = alpha_chars and all(c.isupper() for c in alpha_chars)
                if is_all_uppercase:
                    soft_failures.append(
                        f"Plain message (no ~mention) unexpectedly had skill formatting applied: "
                        f"got {plain_response!r}"
                    )

            with allure.step("Step 6 — ~<skill-name> mention invocation returns UPPER CASE"):
                initial_count = chat.get_message_count()
                chat.send_message_with_skill_mention(
                    SKILL_NAME,
                    NEUTRAL_TEXT_FOR_SKILL,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                chat.wait_for_message_content_stable(
                    stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT,
                )
                mention_response = chat.get_last_message_text()
                logger.info("Uppercase skill response: %r", mention_response)
                alpha_chars = [c for c in mention_response if c.isalpha()]
                assert alpha_chars, (
                    f"~{SKILL_NAME} response contains no alphabetic characters: {mention_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"~{SKILL_NAME} response should be entirely UPPER CASE, got: {mention_response!r}"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed:\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: delete conversation first, then agent, then
            # skill, tolerating individual failures so one bad delete doesn't
            # skip the rest (mirrors ELITEA-1735's teardown pattern).
            if conversation_id is not None:
                try:
                    conversation_api.delete_conversation(int(conversation_id))
                    logger.info("Cleanup: deleted conversation id=%s", conversation_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete conversation id=%s: %s",
                        conversation_id, exc,
                    )
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
