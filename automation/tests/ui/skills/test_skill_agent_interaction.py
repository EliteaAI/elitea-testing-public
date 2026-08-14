"""Interact with Skills from Agent (ELITEA-1735).

Verifies skill invocation modes for agents with attached skills:
1. V1 Explicit invocation: "~<skill-name>" mention syntax triggers the skill
2. V2 Autonomous invocation: skill auto-applies when user message matches
   the skill's description trigger condition
3. Plain messages that don't match any skill's trigger should NOT apply skills

Spec: test-specs/skills/l3_interact-with-skills-from-agent_ELITEA-1735.md
Related: GitHub issue #5698 (Skills V2 - Autonomous Invocation)
"""

import logging

import allure
import pytest

from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

logger = logging.getLogger("elitea.tests.skills")

# Skill 1: Uppercase formatting
# Description is the V2 autonomous trigger condition - LLM reads this to decide relevance
SKILL_1_NAME = "elitea-1735-skill-uppercase"
SKILL_1_DESCRIPTION = (
    "Use this skill ONLY when user explicitly requests FORMAL or POLITE tone"
)
SKILL_1_INSTRUCTIONS = (
    "CRITICAL: You MUST convert ALL text in your response to UPPER CASE letters. "
    "Do NOT use any lowercase letters. Do NOT explain or interpret the text - "
    "just output it in UPPER CASE. Example: 'hello world' becomes 'HELLO WORLD'."
)

# Skill 2: Underscore formatting
SKILL_2_NAME = "elitea-1735-skill-underscore"
SKILL_2_DESCRIPTION = (
    "Use this skill ONLY when user explicitly requests FUN or PLAYFUL formatting"
)
SKILL_2_INSTRUCTIONS = (
    "CRITICAL: You MUST replace ALL spaces between words with underscore _ characters. "
    "Do NOT explain or interpret the text - just output it with underscores. "
    "Example: 'hello world' becomes 'hello_world'."
)

AGENT_NAME = "elitea-1735-skills-agent"

# Plain question - should NOT trigger any skill (no trigger keyword, no ~mention)
PLAIN_QUESTION = "Hello, how are you today?"

# V2 autonomous trigger messages - match skill description trigger conditions
AUTONOMOUS_TRIGGER_FORMAL = "Please respond in a formal polite tone: The quick brown fox"
AUTONOMOUS_TRIGGER_FUN = "Make this fun and playful: The quick brown fox"

# Neutral text for explicit ~mention tests
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


class TestInteractWithSkillsFromAgent:
    """Interact with Skills from Agent (ELITEA-1735, l3/p2).

    Tests both V1 explicit (~mention) and V2 autonomous skill invocation.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1735_interact-with-skills-from-agent.md",
        "onetest-ai Test Case link",
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5698", name="Skills V2 Epic")
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.flaky(reruns=3, reruns_delay=5)
    def test_interact_with_skills_from_agent(self, page, agent_api, skill_api):
        """Create two skills, attach both to an agent, and verify:
        - Plain messages (no trigger) do NOT apply skills
        - V2 autonomous: messages matching skill description trigger the skill
        - V1 explicit: ~<skill-name> mention always triggers the skill

        Steps:
        1. Create Skill 1 (uppercase, triggered by "formal/polite" keywords).
        2. Create Skill 2 (underscore, triggered by "fun/playful" keywords).
        3. Create an Agent.
        4-5. Attach both skills to the agent via the Skills section.
        6. Plain message — should NOT apply any skill formatting.
        7. V2 autonomous trigger for Skill 1 — should return UPPER CASE.
        8. V2 autonomous trigger for Skill 2 — should return underscore_delimited.
        9. V1 explicit ~<Skill 1> mention — should return UPPER CASE.
        10. V1 explicit ~<Skill 2> mention — should return underscore_delimited.
        """
        skill_1_id = None
        skill_2_id = None
        agent_id = None

        try:
            with allure.step("Step 1 — Create Skill 1 (uppercase, formal/polite trigger)"):
                skill_1_id = _create_skill(
                    page, SKILL_1_NAME, SKILL_1_INSTRUCTIONS, SKILL_1_DESCRIPTION
                )

            with allure.step("Step 2 — Create Skill 2 (underscore, fun/playful trigger)"):
                skill_2_id = _create_skill(
                    page, SKILL_2_NAME, SKILL_2_INSTRUCTIONS, SKILL_2_DESCRIPTION
                )
                assert skill_2_id != skill_1_id, (
                    "Skill 2 should have a distinct ID from Skill 1"
                )

            with allure.step("Step 3 — Create Agent"):
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

            with allure.step("Step 4-5 — Attach both skills to the agent"):
                detail_page.attach_skill(SKILL_1_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching Skill 1"
                )
                assert detail_page.is_skill_attached(SKILL_1_NAME), (
                    f"Skill card for '{SKILL_1_NAME}' should render after attaching"
                )

                detail_page.attach_skill(SKILL_2_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "2/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 2 skills attached after attaching Skill 2"
                )
                assert detail_page.is_skill_attached(SKILL_2_NAME), (
                    f"Skill card for '{SKILL_2_NAME}' should render after attaching"
                )

            with allure.step(
                "Step 6 — Plain message (no trigger keywords) should NOT apply skills"
            ):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(PLAIN_QUESTION, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                plain_response = detail_page.get_last_chat_response_text()
                logger.info("Plain response (no trigger): %r", plain_response)

                # Plain question has no trigger keywords (formal/polite/fun/playful)
                # so neither skill should be applied
                alpha_chars = [c for c in plain_response if c.isalpha()]
                is_all_uppercase = alpha_chars and all(c.isupper() for c in alpha_chars)
                has_underscores = "_" in plain_response

                assert not is_all_uppercase, (
                    f"Plain message should NOT trigger uppercase skill: {plain_response!r}"
                )
                assert not has_underscores, (
                    f"Plain message should NOT trigger underscore skill: {plain_response!r}"
                )

            with allure.step(
                "Step 7 — V2 autonomous: 'formal polite' trigger returns UPPER CASE"
            ):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(
                    AUTONOMOUS_TRIGGER_FORMAL, timeout=UI_ELEMENT_TIMEOUT
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                formal_response = detail_page.get_last_chat_response_text()
                logger.info("V2 autonomous formal/polite response: %r", formal_response)
                alpha_chars = [c for c in formal_response if c.isalpha()]
                assert alpha_chars, (
                    f"Formal trigger response has no alphabetic chars: {formal_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"V2 autonomous: 'formal polite' should trigger uppercase skill, "
                    f"got: {formal_response!r}"
                )

            with allure.step(
                "Step 8 — V2 autonomous: 'fun playful' trigger returns underscore_delimited"
            ):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(
                    AUTONOMOUS_TRIGGER_FUN, timeout=UI_ELEMENT_TIMEOUT
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                fun_response = detail_page.get_last_chat_response_text()
                logger.info("V2 autonomous fun/playful response: %r", fun_response)
                assert "_" in fun_response, (
                    f"V2 autonomous: 'fun playful' should trigger underscore skill, "
                    f"got: {fun_response!r}"
                )

            with allure.step("Step 9 — V1 explicit: ~<Skill 1> returns UPPER CASE"):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message_with_mention(
                    SKILL_1_NAME,
                    NEUTRAL_TEXT_FOR_SKILL,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                upper_response = detail_page.get_last_chat_response_text()
                logger.info("V1 explicit ~uppercase response: %r", upper_response)
                alpha_chars = [c for c in upper_response if c.isalpha()]
                assert alpha_chars, (
                    f"~{SKILL_1_NAME} response has no alphabetic chars: {upper_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"V1 explicit ~{SKILL_1_NAME} should return UPPER CASE, "
                    f"got: {upper_response!r}"
                )

            with allure.step("Step 10 — V1 explicit: ~<Skill 2> returns underscore_delimited"):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message_with_mention(
                    SKILL_2_NAME,
                    NEUTRAL_TEXT_FOR_SKILL,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                underscore_response = detail_page.get_last_chat_response_text()
                logger.info("V1 explicit ~underscore response: %r", underscore_response)
                assert "_" in underscore_response, (
                    f"V1 explicit ~{SKILL_2_NAME} should return underscore_delimited, "
                    f"got: {underscore_response!r}"
                )

        finally:
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
            for skill_id in (skill_1_id, skill_2_id):
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%d", skill_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
