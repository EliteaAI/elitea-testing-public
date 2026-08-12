"""Interact with Skills from Conversation (ELITEA-1736).

Verifies skill invocation when the agent is added as a **chat participant**
(a different code path from ELITEA-1735's agent-level embedded chat):
1. V1 Explicit invocation: "~<skill-name>" mention syntax triggers the skill
2. V2 Autonomous invocation: skill auto-applies when user message matches
   the skill's description trigger condition
3. Plain messages that don't match any skill's trigger should NOT apply skills

Spec: test-specs/skills/l3_interact-with-skills-from-conversation_ELITEA-1736.md
Related: GitHub issue #5698 (Skills V2 - Autonomous Invocation)
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

# Skill: Uppercase formatting
# Description is the V2 autonomous trigger condition - LLM reads this to decide relevance
SKILL_NAME = "elitea-1736-uppercase-skill"
SKILL_DESCRIPTION = (
    "Use this skill ONLY when user explicitly requests FORMAL or POLITE tone"
)
SKILL_INSTRUCTIONS = (
    "CRITICAL: You MUST convert ALL text in your response to UPPER CASE letters. "
    "Do NOT use any lowercase letters. Do NOT explain or interpret the text - "
    "just output it in UPPER CASE. Example: 'hello world' becomes 'HELLO WORLD'."
)
AGENT_NAME = "elitea-1736-conversation-agent"

# Plain question - should NOT trigger any skill (no trigger keyword, no ~mention)
PLAIN_QUESTION = "Hello, how are you today?"

# V2 autonomous trigger message - matches skill description trigger condition
AUTONOMOUS_TRIGGER_FORMAL = "Please respond in a formal polite tone: The quick brown fox"

# Neutral text for explicit ~mention test
NEUTRAL_TEXT_FOR_SKILL = "The quick brown fox jumps over the lazy dog"


def _create_skill(page, name: str, instructions: str, description: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Args:
        page: Playwright page instance.
        name: Skill name.
        instructions: Skill instructions (what the skill does).
        description: Skill description - this is the V2 autonomous trigger
            condition that the LLM reads to decide if the skill is relevant.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=description,
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
    """Interact with Skills from Conversation (ELITEA-1736, l3).

    Tests both V1 explicit (~mention) and V2 autonomous skill invocation
    when agent is added as a chat participant.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1736_interact-with-skills-from-conversation.md",
        "onetest-ai Test Case link",
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5698", name="Skills V2 Epic")
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.flaky(reruns=3, reruns_delay=5)
    def test_interact_with_skills_from_conversation(
        self, page, agent_api, skill_api, conversation_api,
    ):
        """Create a skill, attach it to an agent, add the agent as a chat
        participant, and verify:
        - Plain messages (no trigger) do NOT apply skills
        - V2 autonomous: messages matching skill description trigger the skill
        - V1 explicit: ~<skill-name> mention always triggers the skill

        Steps:
        1. Create Skill (uppercase, triggered by "formal/polite" keywords).
        2. Create an Agent.
        3. Attach the skill to the agent via the Skills section.
        4. Open Chat, add the agent as a participant.
        5. Plain message — should NOT apply skill formatting.
        6. V2 autonomous trigger — should return UPPER CASE.
        7. V1 explicit ~<skill-name> — should return UPPER CASE.
        """
        skill_id = None
        agent_id = None
        conversation_id = None

        try:
            with allure.step("Step 1 — Create Skill (uppercase, formal/polite trigger)"):
                skill_id = _create_skill(
                    page, SKILL_NAME, SKILL_INSTRUCTIONS, SKILL_DESCRIPTION
                )

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
                "Step 5 — Plain message (no trigger keywords) should NOT apply skills"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(PLAIN_QUESTION, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                chat.wait_for_message_content_stable(
                    stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT,
                )
                chat.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

                conversation_id = _extract_conversation_id(page)
                assert conversation_id, (
                    "Sending the first message should create a conversation and "
                    f"update the URL to /chat/{{id}} — got {page.url!r}"
                )

                plain_response = chat.get_last_message_text()
                logger.info("Plain response (no trigger): %r", plain_response)
                alpha_chars = [c for c in plain_response if c.isalpha()]

                # Plain question has no trigger keywords (formal/polite)
                # so skill should NOT be applied
                is_all_uppercase = alpha_chars and all(c.isupper() for c in alpha_chars)
                assert not is_all_uppercase, (
                    f"Plain message should NOT trigger uppercase skill: {plain_response!r}"
                )

            with allure.step(
                "Step 6 — V2 autonomous: 'formal polite' trigger returns UPPER CASE"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(AUTONOMOUS_TRIGGER_FORMAL, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                chat.wait_for_message_content_stable(
                    stable_duration_ms=2000, timeout=AI_RESPONSE_TIMEOUT,
                )
                formal_response = chat.get_last_message_text()
                logger.info("V2 autonomous formal/polite response: %r", formal_response)
                alpha_chars = [c for c in formal_response if c.isalpha()]
                assert alpha_chars, (
                    f"Formal trigger response has no alphabetic chars: {formal_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"V2 autonomous: 'formal polite' should trigger uppercase skill, "
                    f"got: {formal_response!r}"
                )

            with allure.step("Step 7 — V1 explicit: ~<skill-name> returns UPPER CASE"):
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
                logger.info("V1 explicit ~uppercase response: %r", mention_response)
                alpha_chars = [c for c in mention_response if c.isalpha()]
                assert alpha_chars, (
                    f"~{SKILL_NAME} response has no alphabetic chars: {mention_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"V1 explicit ~{SKILL_NAME} should return UPPER CASE, "
                    f"got: {mention_response!r}"
                )

        finally:
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
