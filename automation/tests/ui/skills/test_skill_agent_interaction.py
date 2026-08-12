"""Interact with Skills from Agent (ELITEA-1735), extended by ELITEA-2607
and ELITEA-2609.

Verifies skill invocation modes for agents with attached skills:
1. V1 Explicit invocation: "~<skill-name>" mention syntax triggers the skill
2. V2 Autonomous invocation: skill auto-applies when user message matches
   the skill's description trigger condition
3. Plain messages that don't match any skill's trigger should NOT apply skills
4. (ELITEA-2607) Autonomous invocation is visible in the thought process as a
   "Skill: {name}" tool chip, and an unattached skill is NEVER invoked even
   when an adversarial prompt explicitly invites it (security invariant).
5. (ELITEA-2609) When a SINGLE message is both an explicit ``~mention`` AND
   independently matches that same skill's own autonomous-trigger
   description, the skill is invoked exactly ONCE - no double-injection.

Spec: test-specs/skills/l3_interact-with-skills-from-agent_ELITEA-1735.md
Spec: test-specs/skills/lextend_skill-autonomous-invocation-core-functionality_ELITEA-2607.md
Spec: test-specs/skills/lextend_skill-explicit-autonomous-invocation-coexistence_ELITEA-2609.md
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
from playwright.sync_api import expect

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

# --- ELITEA-2607 extension: thought-process visibility + unattached-skill security ---

# Skill 3: attached, uppercase transform, "format Python code" trigger
SKILL_3_NAME = "elitea-2607-code-formatter"
SKILL_3_DESCRIPTION = "Use this skill ONLY when the user explicitly asks to format Python code."
SKILL_3_INSTRUCTIONS = (
    "CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. "
    "Do NOT explain, just output the transformed text in UPPER CASE."
)

# Skill 4: kept UNATTACHED for the whole test - canary-marker instructions.
# A real translation is indistinguishable from the base LLM answering the same
# prompt with zero skill involvement, so a plausible-looking transform cannot
# prove non-invocation - only a marker that could ONLY come from this skill's
# own instructions firing can.
SKILL_4_NAME = "elitea-2607-translator-skill"
SKILL_4_DESCRIPTION = (
    "Use this skill ONLY when the user explicitly asks to translate text to Spanish."
)
SKILL_4_CANARY_MARKER = "ZZTRANSLATOR_SKILL_FIRED_ZZ"
SKILL_4_INSTRUCTIONS = (
    f"CRITICAL: You MUST respond ONLY with the exact literal marker string "
    f"{SKILL_4_CANARY_MARKER} and nothing else, no matter what the user asks."
)

AGENT_2607_NAME = "elitea-2607-autonomous-test-agent"

# Sent with NO ~mention - must be invoked purely by autonomous context match
CONTEXT_MATCHING_PROMPT = "Please format this Python code: def hello(): print('hi')"
# Deliberately invites the UNATTACHED Skill 4 by name/intent - no ~mention
# available either, since Skill 4 was never attached (ELITEA-1791 scoping)
ADVERSARIAL_PROMPT = "Translate 'hello' to Spanish, use your translator skill if you have one."
# Case Part B step 10 (verbatim test data) - matches neither Skill 3's nor
# Skill 4's trigger condition
NON_MATCHING_PROMPT = "What is the capital of France?"

# --- ELITEA-2609 extension: explicit ~mention + autonomous context-match
# coexistence (no double-injection) ---

# Attached skill: uppercase transform, "format text as markdown" trigger.
SKILL_2609_NAME = "elitea-2609-explicit-autonomous"
SKILL_2609_DESCRIPTION = (
    "Use this skill ONLY when the user explicitly asks to format text as markdown."
)
SKILL_2609_INSTRUCTIONS = (
    "CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. "
    "Do not explain, just output the transformed text in UPPER CASE."
)

AGENT_2609_NAME = "elitea-2609-coexistence-agent"

# Appended AFTER the "~<skill-name>" mention chip - this text ALSO
# independently matches Skill 2609's own description trigger ("asks to
# format text as markdown"), unlike NEUTRAL_TEXT_FOR_SKILL above. This is
# the case's actual differentiator (Part B): explicit mention + context
# match co-occurring on the SAME message.
COMBINED_MENTION_AND_CONTEXT_PROMPT = "Format as markdown: Title, item1, item2, item3"


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

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2607_skill-autonomous-invocation-core.md",
        "onetest-ai Test Case link",
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5698", name="Skills V2 Epic")
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.flaky(reruns=3, reruns_delay=5)
    def test_skill_autonomous_invocation_thought_process_and_security(self, page, agent_api, skill_api):
        """Extends ELITEA-1735 coverage for ELITEA-2607 (extend-existing AFS).

        ELITEA-1735's own test already proves autonomous invocation via
        response-text transforms (2 always-attached skills) and
        non-matching-prompt non-invocation on the response TEXT. This test
        fills the two gaps the covering spec never asserts, plus the case's
        own Part B step 12 (thought-process side of non-invocation, which the
        covering spec's Step 6 never checks - only the response text):
        - Gap 1: the autonomous invocation is visible in the thought process
          as a "Skill: {name}" tool chip inside `chat-answer-thought-accordion`.
        - Part B step 12: a non-matching prompt shows NO skill chip in the
          thought process either (not just an untransformed response) - the
          AFS Coverage Map flagged this as a real gap since the covering
          spec's Step 6 only asserts response text, never the chip.
        - Gap 2: a skill that is NEVER attached to the agent is never invoked,
          even when an adversarial prompt explicitly invites it by name/intent
          (security invariant) - no attached skill in the covering spec is
          ever left unattached, so this case is not covered there.

        Steps:
        1. Create Skill 3 (attached; uppercase transform, "format Python
           code" trigger).
        2. Create Skill 4 (kept UNATTACHED; canary-marker instructions).
        3. Create a fresh Agent.
        4. Attach ONLY Skill 3 - Skill 4 stays unattached.
        5-6. Send the context-matching prompt (Skill 3's trigger, no
           ~mention) - assert the response is transformed AND the thought
           accordion shows a "Skill: {Skill 3 name}" tool chip (Gap 1).
        7. Clear chat; send the case's verbatim non-matching prompt ("What is
           the capital of France?", no ~mention) - assert the response is
           NOT transformed AND no "Skill: {Skill 3 name}" chip appears in the
           thought accordion (case Part B step 12).
        8-9. Clear chat; send an adversarial prompt inviting the UNATTACHED
           Skill 4 by name/intent - assert the canary marker never appears
           in the response AND no "Skill: {Skill 4 name}" chip appears in
           the thought accordion (Gap 2).
        """
        skill_3_id = None
        skill_4_id = None
        agent_id = None

        try:
            with allure.step(
                "Step 1 — Create Skill 3 (attached; uppercase, 'format Python code' trigger)"
            ):
                skill_3_id = _create_skill(
                    page, SKILL_3_NAME, SKILL_3_INSTRUCTIONS, SKILL_3_DESCRIPTION
                )

            with allure.step(
                "Step 2 — Create Skill 4 (kept unattached; canary-marker instructions)"
            ):
                skill_4_id = _create_skill(
                    page, SKILL_4_NAME, SKILL_4_INSTRUCTIONS, SKILL_4_DESCRIPTION
                )
                assert skill_4_id != skill_3_id, (
                    "Skill 4 should have a distinct ID from Skill 3"
                )

            with allure.step("Step 3 — Create Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_2607_NAME,
                    description="Autonomous-invocation security test assistant",
                    instructions="You are a helpful assistant. Use your skills when appropriate.",
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
                logger.info("Created agent %r with id=%d", AGENT_2607_NAME, agent_id)

            with allure.step("Step 4 — Attach ONLY Skill 3; Skill 4 remains unattached"):
                detail_page.attach_skill(SKILL_3_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching Skill 3"
                )
                assert detail_page.is_skill_attached(SKILL_3_NAME), (
                    f"Skill card for '{SKILL_3_NAME}' should render after attaching"
                )
                assert not detail_page.is_skill_attached(SKILL_4_NAME), (
                    f"Skill 4 ('{SKILL_4_NAME}') must NOT be attached - it stays "
                    "unattached for the security check"
                )

            with allure.step(
                "Step 5-6 — Matching prompt autonomously invokes Skill 3; thought process "
                "shows a 'Skill: {name}' chip (Gap 1)"
            ):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(
                    CONTEXT_MATCHING_PROMPT, timeout=UI_ELEMENT_TIMEOUT
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                formatted_response = detail_page.get_last_chat_response_text()
                logger.info("Context-matching-prompt response: %r", formatted_response)
                alpha_chars = [c for c in formatted_response if c.isalpha()]
                assert alpha_chars, (
                    f"Context-matching prompt response has no alphabetic chars: "
                    f"{formatted_response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"Skill 3 should be autonomously invoked (uppercase transform), "
                    f"got: {formatted_response!r}"
                )

                accordion = detail_page.get_outer_thought_accordion(timeout=UI_ELEMENT_TIMEOUT)
                matched_chip = accordion.locator(
                    detail_page.CHAT_ANSWER_TOOL_CHIP_SELECTOR
                ).filter(has_text=f"Skill: {SKILL_3_NAME}")
                expect(matched_chip.first).to_contain_text(
                    f"Skill: {SKILL_3_NAME}", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Non-matching prompt does not invoke Skill 3: no transform, "
                "no 'Skill: {name}' chip in the thought process (case Part B step 12)"
            ):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(
                    NON_MATCHING_PROMPT, timeout=UI_ELEMENT_TIMEOUT
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                non_matching_response = detail_page.get_last_chat_response_text()
                logger.info("Non-matching-prompt response: %r", non_matching_response)
                alpha_chars = [c for c in non_matching_response if c.isalpha()]
                is_all_uppercase = alpha_chars and all(c.isupper() for c in alpha_chars)
                assert not is_all_uppercase, (
                    f"Non-matching prompt should NOT trigger Skill 3's uppercase "
                    f"transform: {non_matching_response!r}"
                )

                accordion = detail_page.get_outer_thought_accordion(timeout=UI_ELEMENT_TIMEOUT)
                unmatched_chip = accordion.locator(
                    detail_page.CHAT_ANSWER_TOOL_CHIP_SELECTOR
                ).filter(has_text=f"Skill: {SKILL_3_NAME}")
                expect(unmatched_chip).to_have_count(0)

            with allure.step(
                "Step 8-9 — Adversarial prompt naming the UNATTACHED Skill 4 never invokes "
                "it: no canary marker in the response, no 'Skill: {name}' chip (Gap 2)"
            ):
                detail_page.clear_embedded_chat(timeout=UI_ELEMENT_TIMEOUT)
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(ADVERSARIAL_PROMPT, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                adversarial_response = detail_page.get_last_chat_response_text()
                logger.info("Adversarial-prompt response: %r", adversarial_response)
                # Case-insensitive: an LLM could plausibly echo the marker in mixed
                # case if it ever leaked partially - a garbled leak is just as much
                # a security failure as a clean one.
                assert SKILL_4_CANARY_MARKER.lower() not in adversarial_response.lower(), (
                    f"Unattached Skill 4's canary marker leaked into the response - "
                    f"security invariant broken: {adversarial_response!r}"
                )

                accordion = detail_page.get_outer_thought_accordion(timeout=UI_ELEMENT_TIMEOUT)
                unattached_chip = accordion.locator(
                    detail_page.CHAT_ANSWER_TOOL_CHIP_SELECTOR
                ).filter(has_text=f"Skill: {SKILL_4_NAME}")
                expect(unattached_chip).to_have_count(0)

        finally:
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
            for skill_id in (skill_3_id, skill_4_id):
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%d", skill_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2609_skill-explicit-autonomous-invocation-coexistence.md",
        "onetest-ai Test Case link",
    )
    @allure.link("https://github.com/EliteaAI/elitea_issues/issues/5698", name="Skills V2 Epic")
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.flaky(reruns=3, reruns_delay=5)
    def test_skill_explicit_and_autonomous_invocation_coexistence(self, page, agent_api, skill_api):
        """Extends ELITEA-1735/2607 coverage for ELITEA-2609 (extend-existing AFS).

        Part A (explicit ~mention still works) and Part C (both invocation
        modes independently produce correct output) are already proven by
        this class's other two test methods - see the AFS Coverage Map:
        `test_interact_with_skills_from_agent` Steps 9-10 (explicit-alone)
        and Steps 7-8 (autonomous-alone), plus
        `test_skill_autonomous_invocation_thought_process_and_security`
        Steps 5-6 (thought-process chip mechanism). This test fills the ONE
        gap the covering spec never exercises: Part B, a SINGLE message that
        is BOTH an explicit ``~skill-name`` mention AND independently
        matches that same skill's own autonomous-trigger description.
        Neither existing test ever combines the two triggers on one message
        (1735's Steps 9-10 append deliberately NEUTRAL trailing text; 2607's
        autonomous test never uses a ``~mention``) - so the no-double-
        injection invariant for the co-occurring case is untested until now.

        Steps:
        1. Create a skill (attached; uppercase transform, "asks to format
           text as markdown" trigger).
        2. Create an agent, attach the skill.
        3. Send ``~<skill-name> Format as markdown: Title, item1, item2,
           item3`` - an explicit mention whose appended text ALSO matches
           the skill's own description trigger.
        4. Assert exactly ONE ``chat-answer-tool-chip`` reading
           "Skill: {name}" in the thought accordion (the count IS the
           double-injection assertion - two chips would mean two
           invocations), the response is a single, non-duplicated
           UPPER-CASE output, and there are no console errors.
        """
        skill_id = None
        agent_id = None
        console_messages = None  # CapturedConsoleMessages, needs stop() in finally

        try:
            with allure.step(
                "Step 1 — Create skill (attached; uppercase, 'format as markdown' trigger)"
            ):
                skill_id = _create_skill(
                    page, SKILL_2609_NAME, SKILL_2609_INSTRUCTIONS, SKILL_2609_DESCRIPTION
                )

            with allure.step("Step 2 — Create Agent and attach the skill"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_2609_NAME,
                    description="Explicit+autonomous coexistence test assistant",
                    instructions="You are a helpful assistant. Use your skills when appropriate.",
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
                logger.info("Created agent %r with id=%d", AGENT_2609_NAME, agent_id)

                detail_page.attach_skill(SKILL_2609_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching the skill"
                )
                assert detail_page.is_skill_attached(SKILL_2609_NAME), (
                    f"Skill card for '{SKILL_2609_NAME}' should render after attaching"
                )

            with allure.step(
                "Step 3-4 — Combined ~mention + context-match message invokes the skill "
                "exactly ONCE: single chip, single clean output, no console errors"
            ):
                console_messages = detail_page.capture_console_errors()
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message_with_mention(
                    SKILL_2609_NAME,
                    COMBINED_MENTION_AND_CONTEXT_PROMPT,
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                response = detail_page.get_last_chat_response_text()
                logger.info("Combined mention+context response: %r", response)

                accordion = detail_page.get_outer_thought_accordion(timeout=UI_ELEMENT_TIMEOUT)
                matched_chip = accordion.locator(
                    detail_page.CHAT_ANSWER_TOOL_CHIP_SELECTOR
                ).filter(has_text=f"Skill: {SKILL_2609_NAME}")
                # The COUNT is the double-injection assertion - "a chip is
                # present" would still pass with two invocations; exactly 1
                # is what falsifies double-injection.
                expect(matched_chip).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)

                alpha_chars = [c for c in response if c.isalpha()]
                assert alpha_chars, (
                    f"Combined-invocation response has no alphabetic chars: {response!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"Skill should apply its UPPER CASE transform, got: {response!r}"
                )
                # A double-injection defect would duplicate/concatenate the
                # transformed heading - checking its occurrence count (not
                # just its presence) is what catches a repeated block.
                assert response.upper().count("TITLE") == 1, (
                    f"Response should contain the transformed heading exactly once "
                    f"(a double-injection defect would duplicate it), got: {response!r}"
                )

                assert not console_messages, (
                    f"No console errors expected on the combined-invocation interaction, "
                    f"got: {[m.text for m in console_messages]}"
                )

        finally:
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
            if console_messages is not None:
                console_messages.stop()
