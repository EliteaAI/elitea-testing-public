"""Interact with Skills from Agent (ELITEA-1735).

Verifies that skills attached to an agent can be invoked selectively via
the "~<skill-name>" mention syntax, and that a plain message (no mention)
does not apply any attached skill's formatting.

Spec: test-specs/skills/l3_interact-with-skills-from-agent_ELITEA-1735.md
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

pytestmark = [pytest.mark.ui, pytest.mark.skills]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

logger = logging.getLogger("elitea.tests.skills")

SKILL_1_NAME = "elitea-1735-skill-uppercase"
SKILL_1_INSTRUCTIONS = (
    "Always respond with the exact text the user asked for, but convert the "
    "ENTIRE output to UPPER CASE letters. Do not use any lowercase letters "
    "in your response."
)
SKILL_2_NAME = "elitea-1735-skill-underscore"
SKILL_2_INSTRUCTIONS = (
    "Always respond with the exact text the user asked for, but replace "
    "every space between words with an underscore character _ so the "
    "output is underscore_delimited like_this."
)
AGENT_NAME = "elitea-1735-skills-agent"

# Plain question for Step 6 - agent should answer normally without applying skills
PLAIN_QUESTION = "Hello, how are you today?"

# Neutral text for skill mention tests (Steps 7-8)
# Skills will transform this text literally according to their instructions
NEUTRAL_TEXT_FOR_SKILL = "The quick brown fox jumps over the lazy dog"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow in test_skill_management.py: fill the form
    (name / description / CodeMirror instructions), save, and confirm the
    nav-blocker dialog that fires on every save from the create form.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=f"ELITEA-1735 automation skill — {name}",
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
    """Interact with Skills from Agent (ELITEA-1735, l3/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1735_interact-with-skills-from-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_interact_with_skills_from_agent(self, page, agent_api, skill_api):
        """Create two skills, attach both to an agent, and verify selective
        invocation via the "~<skill-name> <prompt>" mention syntax.

        Steps (AFS test-specs/skills/l3_interact-with-skills-from-agent_ELITEA-1735.md):
        1. Create Skill 1 (uppercase-formatting instructions).
        2. Create Skill 2 (underscore-formatting instructions).
        3. Create an Agent.
        4-5. Attach both skills to the agent via the Skills section.
        6. Send a plain message (no mention) — should NOT apply skill formatting.
        7. Send "~<skill-1> <prompt>" — should return entirely UPPER CASE.
        8. Send "~<skill-2> <prompt>" — should return underscore-delimited.
        """
        skill_1_id = None
        skill_2_id = None
        agent_id = None
        # Soft failures list — record failures here instead of raising immediately,
        # so steps 7-8 still execute and report. If anything landed here, the test
        # fails at the very end via pytest.fail().
        soft_failures = []

        try:
            with allure.step("Step 1 — Create Skill 1 (uppercase-formatting instructions)"):
                skill_1_id = _create_skill(page, SKILL_1_NAME, SKILL_1_INSTRUCTIONS)

            with allure.step("Step 2 — Create Skill 2 (underscore-formatting instructions)"):
                skill_2_id = _create_skill(page, SKILL_2_NAME, SKILL_2_INSTRUCTIONS)
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
                    description="ELITEA-1735 automation agent — skill interaction",
                    instructions="You are a helpful assistant.",
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
                "Step 6 — Plain message (no mention) should NOT apply skill formatting"
            ):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(PLAIN_QUESTION, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                plain_response = detail_page.get_last_chat_response_text()
                logger.info("Plain response (no mention): %r", plain_response)

                # Without ~mention, agent should NOT apply skill formatting.
                # The response should be a normal agent reply (asking what to do
                # with the text), NOT the input text transformed by skills.
                alpha_chars = [c for c in plain_response if c.isalpha()]

                # Check that skills were NOT applied (response is not all uppercase)
                is_all_uppercase = alpha_chars and all(c.isupper() for c in alpha_chars)
                # Check that underscore skill was NOT applied
                has_underscores = "_" in plain_response

                # Plain question should get a normal response, not skill-formatted
                if is_all_uppercase and has_underscores:
                    soft_failures.append(
                        f"Plain message (no ~mention) unexpectedly had skill formatting applied: "
                        f"got {plain_response!r}"
                    )
                elif is_all_uppercase:
                    soft_failures.append(
                        f"Plain message appears to have uppercase skill applied: "
                        f"got {plain_response!r}"
                    )

            with allure.step("Step 7 — ~<Skill 1> mention invocation returns UPPER CASE"):
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
                logger.info("Uppercase skill response: %r", upper_response)
                alpha_chars = [c for c in upper_response if c.isalpha()]
                assert alpha_chars, (
                    f"~{SKILL_1_NAME} response contains no alphabetic characters: {upper_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"~{SKILL_1_NAME} response should be entirely UPPER CASE, got: {upper_response!r}"
                )

            with allure.step("Step 8 — ~<Skill 2> mention invocation returns underscore-delimited"):
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
                logger.info("Underscore skill response: %r", underscore_response)
                assert "_" in underscore_response, (
                    f"~{SKILL_2_NAME} response should use '_' between words, "
                    f"got: {underscore_response!r}"
                )
                alpha_chars = [c for c in underscore_response if c.isalpha()]
                assert not (alpha_chars and all(c.isupper() for c in alpha_chars)), (
                    f"~{SKILL_2_NAME} response should NOT be forced UPPER CASE "
                    f"(that is Skill 1's formatting), got: {underscore_response!r}"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed:\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: delete agent first (teardown hygiene), then both
            # skills, tolerating individual failures so one bad delete doesn't
            # skip the rest (mirrors the clean_skill fixture pattern in
            # test_skill_management.py).
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
