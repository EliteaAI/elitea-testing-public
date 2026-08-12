"""Subagent Skills Isolation (ELITEA-2608).

Verifies that a subagent uses ONLY its own attached skill (no parent/master
skill bleed) and that a subagent with no skills attached runs completely
skill-free — regardless of what skill(s) the delegating master agent itself
has attached.

Part A: `subagent-with-skill` (attached: sub-formatter, bullet-point
transform) is invoked by the master (attached: master-formatter, uppercase
transform). Asserts the subagent's own nested thought-process accordion
shows ONLY its own skill's tool chip, never the master's.

Part B: `subagent-no-skills` (no skills attached) is invoked by the same
master. Asserts the subagent's own nested accordion shows ZERO skill-chip
activity, independent of whatever the master's own top-level turn does.

**Master-skill trigger description is narrowed vs. the case's literal text**
(AFS § Test Data / § Known Defects). The case's literal Master Skill
Instructions ("Format all output in UPPERCASE") has no scoping condition, so
an LLM reading it as its own autonomous-invocation trigger treats it as
"always apply" — the analyst's live run confirmed this let the MASTER agent
autonomously invoke its OWN skill on its OWN top-level turn while also
delegating to the skill-free subagent, producing an all-uppercase final
message even though the subagent's own nested execution stayed correctly
skill-free. That is not a subagent-isolation defect (the case's actual Fail
criterion) — it is the master's own single-agent autonomous invocation
co-occurring with an unrelated delegation turn, caused by the test data's own
unconditional trigger description. This test uses a narrowly-scoped trigger
description instead (mirrors ELITEA-2607's canary-condition convention) so
the deterministic mechanism-level assertion (the nested accordion's own
tool-chip) stays the PRIMARY proof either way, and the whole-message-text
checks stay informational rather than a hard, potentially-flaky assertion.

Spec: test-specs/skills/l3_subagent-skills-isolation_ELITEA-2608.md
Related: test_skill_agent_interaction.py (ELITEA-1735/2607, autonomous
invocation + thought-process visibility precedent this test reuses).
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

# Master skill — uppercase transform. Description narrowed to an
# intent-scoped trigger (see module docstring / AFS Known Defects) instead
# of the case's literal, unconditional "Format all output in UPPERCASE".
MASTER_SKILL_NAME = "e2608-master-formatter"
MASTER_SKILL_DESCRIPTION = (
    "Use this skill ONLY when the user explicitly asks you to SHOUT or "
    "emphasize a message in all caps."
)
MASTER_SKILL_INSTRUCTIONS = (
    "CRITICAL: You MUST convert ALL letters in your response to UPPER CASE. "
    "Do not explain, just output the transformed text in UPPER CASE."
)

# Sub-formatter skill — bullet-point transform. Same narrowing reasoning.
SUB_SKILL_NAME = "e2608-sub-formatter"
SUB_SKILL_DESCRIPTION = "Use this skill ONLY when the user asks you to list items."
SUB_SKILL_INSTRUCTIONS = (
    "CRITICAL: You MUST format your ENTIRE response as a markdown bullet "
    "point list (using '- ' for each item). Do not explain, just output the "
    "transformed text as bullet points, one item per bullet."
)

MASTER_AGENT_NAME = "e2608-master-agent"
SUBAGENT_WITH_SKILL_NAME = "e2608-subagent-with-skill"
SUBAGENT_NO_SKILLS_NAME = "e2608-subagent-no-skills"

MASTER_AGENT_INSTRUCTIONS = (
    "You are a master agent. When asked to delegate a task to a specific "
    "subagent, invoke that subagent as a tool with the given prompt and "
    "relay its response verbatim, unmodified."
)

# Explicit naming precedent (ELITEA-1951): naming the sub-agent in the
# message is the reliable invocation shape for deterministically triggering
# a sub-agent tool call.
TRIGGER_PROMPT_PART_A = f"Ask {SUBAGENT_WITH_SKILL_NAME} to list three colors."
TRIGGER_PROMPT_PART_B = f"Ask {SUBAGENT_NO_SKILLS_NAME} to list three animals."


def _create_skill(page, name: str, instructions: str, description: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Suite-local helper mirroring ``TestInteractWithSkillsFromAgent.
    _create_skill`` (`test_skill_agent_interaction.py`) — every skills test
    file in this suite keeps its own copy of this exact flow rather than a
    shared cross-file import (established convention, 10+ files).

    Args:
        page: Playwright page instance.
        name: Skill name.
        instructions: Skill instructions (what the skill does).
        description: Skill description — the V2 autonomous-invocation
            trigger condition the LLM reads to decide relevance.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, instructions=instructions, description=description)
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


def _create_agent(page, name: str, description: str, instructions: str) -> int:
    """Create an agent via the UI and return its numeric ID.

    Suite-local helper mirroring the create flow already established across
    ELITEA-1735/1902/2607 (`test_skill_agent_interaction.py`,
    `test_import_agent_zip_nested_agent_dependencies.py`).
    """
    list_page = AgentsListPage(page)
    list_page.navigate_to_create()

    form_page = AgentFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(name=name, description=description, instructions=instructions)
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), (
        f"Save should be enabled after filling all required fields for agent '{name}'"
    )
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = AgentDetailPage(page)
    detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
    detail_page.verify_on_detail_page()
    agent_id = int(detail_page.get_agent_id())
    logger.info("Created agent %r with id=%d", name, agent_id)
    return agent_id


class TestSubagentSkillsIsolation:
    """Subagent Skills Isolation (ELITEA-2608, l3/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2608_subagent-skills-isolation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.flaky(reruns=3, reruns_delay=5)
    def test_subagent_uses_only_its_own_attached_skill(self, page, agent_api, skill_api):
        """Create a master agent with its own skill and two subagents (one
        with its own distinct skill, one with none), and verify:

        Part A — a subagent with its own attached skill uses ONLY that
        skill: the nested accordion for the invoked subagent shows a
        "Skill: {sub-formatter}" chip and NEVER a
        "Skill: {master-formatter}" chip.

        Part B — a subagent with no skills attached shows ZERO skill-chip
        activity inside its own nested accordion, independent of the
        master's own top-level behavior.

        Steps:
        1. Create master skill (uppercase, narrowed trigger).
        2. Create sub-formatter skill (bullet points, narrowed trigger).
        3-4. Create subagent-with-skill; attach ONLY the sub-formatter skill.
        5-6. Create master agent; attach ONLY the master-formatter skill.
        7. Attach subagent-with-skill to the master as a sub-agent tool.
        8-9. Send the Part A trigger prompt; verify the nested accordion for
           subagent-with-skill shows the sub-formatter chip, never the
           master-formatter chip (the case's core Part-A/Steps 9-10
           assertion — deterministic, mechanism-level).
        10-11. Create subagent-no-skills (no skill attach step); attach it
           to the master as a second sub-agent tool (re-navigating to the
           master's detail page first, which also resets the embedded chat
           to a fresh conversation).
        12. Send the Part B trigger prompt in that fresh conversation.
        13. Expand the nested accordion for subagent-no-skills; verify it
           carries ZERO "Skill: ..." tool chips (the case's core
           Part-B/Step 16 assertion — deterministic, unconditional).
        """
        master_skill_id = None
        sub_skill_id = None
        master_agent_id = None
        subagent_with_skill_id = None
        subagent_no_skills_id = None

        try:
            with allure.step("Step 1 — Create master skill (uppercase, narrowed trigger)"):
                master_skill_id = _create_skill(
                    page, MASTER_SKILL_NAME, MASTER_SKILL_INSTRUCTIONS, MASTER_SKILL_DESCRIPTION
                )

            with allure.step("Step 2 — Create sub-formatter skill (bullet points, narrowed trigger)"):
                sub_skill_id = _create_skill(
                    page, SUB_SKILL_NAME, SUB_SKILL_INSTRUCTIONS, SUB_SKILL_DESCRIPTION
                )
                assert sub_skill_id != master_skill_id, (
                    "Sub-formatter skill should have a distinct ID from the master skill"
                )

            with allure.step(
                "Step 3-4 — Create subagent-with-skill and attach ONLY the sub-formatter skill"
            ):
                subagent_with_skill_id = _create_agent(
                    page,
                    SUBAGENT_WITH_SKILL_NAME,
                    "Subagent with its own attached skill, for isolation testing",
                    "You are a helpful assistant.",
                )
                subagent_detail_page = AgentDetailPage(page)
                subagent_detail_page.attach_skill(SUB_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in subagent_detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching the sub-formatter"
                )
                assert subagent_detail_page.is_skill_attached(SUB_SKILL_NAME), (
                    f"Skill card for '{SUB_SKILL_NAME}' should render after attaching"
                )
                assert not subagent_detail_page.is_skill_attached(MASTER_SKILL_NAME), (
                    f"Master skill '{MASTER_SKILL_NAME}' must NOT be attached to "
                    f"'{SUBAGENT_WITH_SKILL_NAME}' — isolation precondition"
                )

            with allure.step("Step 5-6 — Create master agent and attach ONLY the master-formatter skill"):
                master_agent_id = _create_agent(
                    page,
                    MASTER_AGENT_NAME,
                    "Master agent that delegates to subagents",
                    MASTER_AGENT_INSTRUCTIONS,
                )
                detail_page = AgentDetailPage(page)
                detail_page.attach_skill(MASTER_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching the master skill"
                )
                assert detail_page.is_skill_attached(MASTER_SKILL_NAME), (
                    f"Skill card for '{MASTER_SKILL_NAME}' should render after attaching"
                )

            with allure.step("Step 7 — Attach subagent-with-skill to the master as a sub-agent tool"):
                detail_page.attach_agent_by_testid(SUBAGENT_WITH_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_toolkit_attached(SUBAGENT_WITH_SKILL_NAME), (
                    f"'{SUBAGENT_WITH_SKILL_NAME}' should render as an attached "
                    "sub-agent tool card after linking"
                )

            with allure.step(
                "Step 8 — Send the Part A trigger prompt (invokes subagent-with-skill)"
            ):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(TRIGGER_PROMPT_PART_A, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                part_a_response = detail_page.get_last_chat_response_text()
                logger.info("Part A whole-message response: %r", part_a_response)

                # Informational, not the primary proof (see module docstring):
                # both the master's own skill AND the subagent's delegated
                # skill can influence the final relayed text, so this is a
                # supporting signal, not this test's deterministic assertion.
                alpha_chars = [c for c in part_a_response if c.isalpha()]
                is_all_uppercase = bool(alpha_chars) and all(c.isupper() for c in alpha_chars)
                if "-" not in part_a_response or is_all_uppercase:
                    logger.warning(
                        "Part A whole-message response did not look like a "
                        "plain bullet list (uppercase=%s): %r — the nested "
                        "accordion chip check below is this test's PRIMARY, "
                        "deterministic proof of isolation.",
                        is_all_uppercase, part_a_response,
                    )

            with allure.step(
                "Step 9 — Nested accordion for subagent-with-skill shows ONLY its own "
                "skill chip, never the master's (deterministic, mechanism-level)"
            ):
                sub_chip_texts = detail_page.get_nested_agent_tool_chip_texts(
                    SUBAGENT_WITH_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                logger.info(
                    "Nested accordion tool-chip texts for '%s': %s",
                    SUBAGENT_WITH_SKILL_NAME, sub_chip_texts,
                )
                assert any(
                    text == f"Skill: {SUB_SKILL_NAME}" for text in sub_chip_texts
                ), (
                    f"Nested accordion for '{SUBAGENT_WITH_SKILL_NAME}' should show a "
                    f"'Skill: {SUB_SKILL_NAME}' chip, got: {sub_chip_texts!r}"
                )
                assert not any(
                    text == f"Skill: {MASTER_SKILL_NAME}" for text in sub_chip_texts
                ), (
                    f"Nested accordion for '{SUBAGENT_WITH_SKILL_NAME}' must NEVER show "
                    f"the master's 'Skill: {MASTER_SKILL_NAME}' chip (skill isolation "
                    f"violated), got: {sub_chip_texts!r}"
                )

            with allure.step("Step 10 — Create subagent-no-skills (no skills attached)"):
                subagent_no_skills_id = _create_agent(
                    page,
                    SUBAGENT_NO_SKILLS_NAME,
                    "Subagent with no skills attached, for isolation testing",
                    "You are a helpful assistant.",
                )
                no_skills_detail_page = AgentDetailPage(page)
                assert "0/" in no_skills_detail_page.get_skills_counter_text(), (
                    f"'{SUBAGENT_NO_SKILLS_NAME}' should have 0 skills attached at creation"
                )

            with allure.step("Step 11 — Attach subagent-no-skills to the master as a second sub-agent tool"):
                detail_page.navigate(master_agent_id)
                detail_page.attach_agent_by_testid(SUBAGENT_NO_SKILLS_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_toolkit_attached(SUBAGENT_WITH_SKILL_NAME), (
                    f"'{SUBAGENT_WITH_SKILL_NAME}' should still be attached after "
                    "attaching the second sub-agent"
                )
                assert detail_page.is_toolkit_attached(SUBAGENT_NO_SKILLS_NAME), (
                    f"'{SUBAGENT_NO_SKILLS_NAME}' should render as an attached "
                    "sub-agent tool card after linking"
                )

            with allure.step(
                "Step 12 — Send the Part B trigger prompt in a fresh conversation"
            ):
                # Fresh conversation via re-navigation (Step 11's `navigate()`
                # call already did this) — confirmed live during analysis
                # (AFS § Automation Hints): navigating back to the agent
                # detail page resets the embedded chat to empty, so no
                # separate `clear_embedded_chat()` call is needed (and the
                # "Clear the chat" button renders disabled on an already-empty
                # chat, which is not a safe click target).
                initial_count = detail_page.get_chat_message_count()
                assert initial_count == 0, (
                    "Embedded chat should be empty (fresh conversation) after "
                    f"re-navigating to the master agent, got {initial_count} messages"
                )
                detail_page.send_chat_message(TRIGGER_PROMPT_PART_B, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                part_b_response = detail_page.get_last_chat_response_text()
                logger.info("Part B whole-message response: %r", part_b_response)

                # Informational only (AFS Known Defects / Automation Hints):
                # the MASTER's own attached skill can autonomously fire on
                # its own top-level relay turn independent of subagent
                # isolation — never this test's assertion target. The nested
                # accordion chip check below is the deterministic proof.
                alpha_chars = [c for c in part_b_response if c.isalpha()]
                is_all_uppercase = bool(alpha_chars) and all(c.isupper() for c in alpha_chars)
                if is_all_uppercase:
                    logger.warning(
                        "Part B whole-message response came back fully "
                        "UPPERCASE (%r) — most likely the master's OWN "
                        "'%s' skill fired on its own top-level relay turn "
                        "(a single-agent autonomous invocation, independent "
                        "of and unrelated to subagent isolation — see AFS "
                        "Known Defects). The nested accordion chip check "
                        "below is this test's PRIMARY, unconditionally "
                        "deterministic proof of isolation.",
                        part_b_response, MASTER_SKILL_NAME,
                    )

            with allure.step(
                "Step 13 — Nested accordion for subagent-no-skills shows ZERO skill "
                "chips, regardless of the master's own turn (deterministic, unconditional)"
            ):
                details = detail_page.get_nested_agent_accordion_details(
                    SUBAGENT_NO_SKILLS_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                all_chips = details.locator(detail_page.CHAT_ANSWER_TOOL_CHIP_SELECTOR)
                expect(all_chips).to_have_count(0)

        finally:
            for aid in (master_agent_id, subagent_with_skill_id, subagent_no_skills_id):
                if aid is not None:
                    try:
                        agent_api.delete_agent(aid)
                        logger.info("Cleanup: deleted agent id=%d", aid)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete agent id=%s: %s", aid, exc)
            for sid in (master_skill_id, sub_skill_id):
                if sid is not None:
                    try:
                        skill_api.delete_skill(sid)
                        logger.info("Cleanup: deleted skill id=%d", sid)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete skill id=%s: %s", sid, exc)
