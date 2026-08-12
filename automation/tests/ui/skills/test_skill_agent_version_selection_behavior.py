"""Test — Skill version selection behaviour drives the agent's live chat (ELITEA-2610).

Verifies that when a specific NON-BASE skill version is attached to an agent,
that version's instructions govern the agent's autonomous chat invocation of
the skill — and that switching the attached version updates behaviour on the
very NEXT chat turn, in the SAME conversation, with no page reload, no new
chat, and no explicit agent-level Save.

This is genuinely new ground vs the two closest neighbours:
- `test_skill_agent_version_selector.py` (ELITEA-1789) proves the version
  selector renders, shows the default (`base`), and opens a real menu — but
  that skill only ever had ONE saved version, so actually SELECTING a
  non-base option was never exercised there.
- `test_skill_test_panel_version_instructions.py` (ELITEA-2440) proves
  version-switching changes the response inside the Skill's OWN
  `SkillTestPanel` — a different surface from the agent's live chat, where
  the skill is invoked autonomously as one of the agent's tools.

Uses deterministic marker-tag instructions (`[BASE-STYLE]:` / `[CASUAL-STYLE]:`
/ `[TECH-STYLE]:`) instead of the case's literal subjective tone prose — an
assertion on "casual tone" isn't reliably scriptable; a marker tag is. Mirrors
the ELITEA-2440 deterministic-marker pattern.

Spec: test-specs/skills/l3_skill-version-selection-behavior_ELITEA-2610.md
"""

import logging
import re
import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

logger = logging.getLogger("elitea.tests.skills")

FORM_SAVE_TIMEOUT = 15_000
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

# uuid4 suffix (not a truncated timestamp) — real per-run entropy that survives
# the 32-char name cap (constants.js MAX_NAME_LENGTH), matching the established
# `_SUFFIX = uuid.uuid4().hex[:6]` pattern in this dir (e.g.
# test_published_agent_version_cannot_be_modified.py). Applying `[:32]` AFTER
# concatenating a full name+timestamp string (the prior shape here) sliced off
# the differentiating suffix digits instead of the base name, so two runs
# started in the same ~1-day window collided on name — fixed by building each
# name short enough, by construction, to never need a post-hoc slice.
_SUFFIX = uuid.uuid4().hex[:6]
SKILL_NAME = f"el-2610-resp-style-{_SUFFIX}"
AGENT_NAME = f"el-2610-ver-behavior-{_SUFFIX}"
TEST_PROMPT = "Explain what an API is"

SKILL_DESCRIPTION = "Use this skill for EVERY user question, no matter the topic."

BASE_INSTRUCTIONS = (
    "Start every response with the exact tag [BASE-STYLE] followed by a "
    "colon, then answer formally."
)
CASUAL_INSTRUCTIONS = (
    "Start every response with the exact tag [CASUAL-STYLE] followed by a "
    "colon, then answer in a casual tone with emojis."
)
TECH_INSTRUCTIONS = (
    "Start every response with the exact tag [TECH-STYLE] followed by a "
    "colon, then answer with technical details, and include a short code "
    "example immediately preceded by the exact literal tag [CODE-EXAMPLE] "
    "on its own line."
)

# Broad-enough emoji heuristic (common pictograph/symbol/dingbat blocks) — the
# model chooses its own emoji, so this asserts "an emoji is present", not a
# specific character. Suite-local helper (single call site).
_EMOJI_PATTERN = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)


class TestSkillAgentVersionSelectionBehavior:
    """ELITEA-2610 — attached skill version governs the agent's live chat behaviour."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2610_skill-version-selection-behavior.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_skill_version_selection_drives_agent_chat_behavior(
        self, page, agent_api, skill_api,
    ):
        """Create a 3-version skill + an agent that attaches it, then prove:

        Part A — attaching + selecting the `casual` (non-base) version makes
        the agent's autonomous chat invocation use THAT version's behaviour.
        Part B — switching the attached version to `technical` updates
        behaviour on the very next turn, same conversation, no reload/Save.
        Part C — switching back to `base` reverts behaviour the same way.
        """
        skill_id = None
        agent_id = None

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                "Step 1 — Create the Skill with base-version instructions (deterministic marker tag)"
            ):
                list_page = SkillsListPage(page)
                list_page.navigate_to_create()

                form_page = SkillFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=SKILL_NAME,
                    instructions=BASE_INSTRUCTIONS,
                    description=SKILL_DESCRIPTION,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required skill fields"
                )
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = SkillDetailPage(page)
                detail_page.verify_on_detail_page()
                skill_id = int(detail_page.get_skill_id())
                logger.info("Created skill %r id=%d", SKILL_NAME, skill_id)

            with allure.step("Step 2 — Save As Version 'casual' with casual-style instructions"):
                detail_page.fill_instructions(CASUAL_INSTRUCTIONS)
                detail_page.save_as_version("casual")

            with allure.step("Step 3 — Save As Version 'technical' with technical-style instructions"):
                detail_page.fill_instructions(TECH_INSTRUCTIONS)
                detail_page.save_as_version("technical")

            with allure.step("Step 4 — Create the Agent"):
                agents_list_page = AgentsListPage(page)
                agents_list_page.navigate_to_create()

                agent_form_page = AgentFormPage(page)
                agent_form_page.wait_for_form_load()
                agent_form_page.fill_form(
                    name=AGENT_NAME,
                    description="ELITEA-2610 automation agent — version selection behaviour",
                    instructions="You are a helpful assistant. Use your skills when appropriate.",
                )
                agent_form_page.wait_for_form_validation()
                assert agent_form_page.is_save_enabled(), (
                    "Save should be enabled after filling all required agent fields"
                )
                agent_form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                agent_detail_page = AgentDetailPage(page)
                agent_detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                agent_detail_page.verify_on_detail_page()
                agent_id = int(agent_detail_page.get_agent_id())
                logger.info("Created agent %r id=%d", AGENT_NAME, agent_id)

            with allure.step("Step 5 — Attach the Skill to the Agent (defaults to 'base')"):
                agent_detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                agent_detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in agent_detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert agent_detail_page.get_skill_version_text(SKILL_NAME) == "base", (
                    "Newly attached skill should default to the 'base' version"
                )

            with allure.step(
                "Step 6 — Select the 'casual' version from the attached skill's Versions menu"
            ):
                agent_detail_page.select_skill_version(
                    SKILL_NAME, "casual", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert agent_detail_page.get_skill_version_text(SKILL_NAME) == "casual", (
                    "Version selector trigger should show 'casual' after selection"
                )

            with allure.step(
                "Step 7-8 — Open the embedded chat (already on this page) and send the test prompt"
            ):
                initial_count = agent_detail_page.get_chat_message_count()
                agent_detail_page.send_chat_message(TEST_PROMPT, timeout=UI_ELEMENT_TIMEOUT)
                agent_detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )

            with allure.step(
                "Step 9-10 — Response uses the CASUAL version's behaviour "
                "(marker tag + emoji present, autonomous invocation confirmed)"
            ):
                response_casual = agent_detail_page.get_last_chat_response_text()
                assert response_casual.startswith("[CASUAL-STYLE]:"), (
                    f"Expected the casual-version response to start with "
                    f"'[CASUAL-STYLE]:', got: {response_casual!r}"
                )
                assert _EMOJI_PATTERN.search(response_casual), (
                    f"Expected the casual-version response to contain an emoji, "
                    f"got: {response_casual!r}"
                )
                assert "[BASE-STYLE]" not in response_casual, (
                    f"Casual-version response should NOT contain '[BASE-STYLE]', "
                    f"got: {response_casual!r}"
                )
                chip_texts = agent_detail_page.get_last_message_tool_chip_texts(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert chip_texts == [f"Skill: {SKILL_NAME}"], (
                    f"Expected the last message's tool chip to read "
                    f"'Skill: {SKILL_NAME}' (autonomous invocation), got: {chip_texts!r}"
                )

            with allure.step(
                "Step 11 (Part B) — Switch the attached version to 'technical', no navigation needed"
            ):
                agent_detail_page.select_skill_version(
                    SKILL_NAME, "technical", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert agent_detail_page.get_skill_version_text(SKILL_NAME) == "technical", (
                    "Version selector trigger should show 'technical' after selection"
                )

            with allure.step(
                "Step 12 — Send the SAME prompt again in the SAME conversation "
                "(no reload, no new chat, no explicit agent-level Save)"
            ):
                initial_count = agent_detail_page.get_chat_message_count()
                agent_detail_page.send_chat_message(TEST_PROMPT, timeout=UI_ELEMENT_TIMEOUT)
                agent_detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )

            with allure.step(
                "Step 13-14 — Very next turn uses the TECHNICAL version's behaviour, "
                "NOT a repeat of the casual response"
            ):
                response_technical = agent_detail_page.get_last_chat_response_text()
                assert response_technical.startswith("[TECH-STYLE]:"), (
                    f"Expected the technical-version response to start with "
                    f"'[TECH-STYLE]:', got: {response_technical!r}"
                )
                assert "[CODE-EXAMPLE]" in response_technical, (
                    f"Expected the technical-version response to contain the "
                    f"'[CODE-EXAMPLE]' marker preceding its code example, "
                    f"got: {response_technical!r}"
                )
                assert "[CASUAL-STYLE]" not in response_technical, (
                    f"Technical-version response should NOT contain "
                    f"'[CASUAL-STYLE]', got: {response_technical!r}"
                )
                chip_texts = agent_detail_page.get_last_message_tool_chip_texts(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert chip_texts == [f"Skill: {SKILL_NAME}"], (
                    f"Expected the last message's tool chip to read "
                    f"'Skill: {SKILL_NAME}' (autonomous invocation), got: {chip_texts!r}"
                )

            with allure.step("Step 15 (Part C) — Revert the attached version to 'base'"):
                agent_detail_page.select_skill_version(
                    SKILL_NAME, "base", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert agent_detail_page.get_skill_version_text(SKILL_NAME) == "base", (
                    "Version selector trigger should show 'base' after reverting"
                )

            with allure.step("Step 16 — Send the SAME prompt a third time, same conversation"):
                initial_count = agent_detail_page.get_chat_message_count()
                agent_detail_page.send_chat_message(TEST_PROMPT, timeout=UI_ELEMENT_TIMEOUT)
                agent_detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )

            with allure.step(
                "Step 17 — Third turn reverts to the BASE version's formal, non-casual behaviour"
            ):
                response_base = agent_detail_page.get_last_chat_response_text()
                assert response_base.startswith("[BASE-STYLE]:"), (
                    f"Expected the base-version response to start with "
                    f"'[BASE-STYLE]:', got: {response_base!r}"
                )
                assert not _EMOJI_PATTERN.search(response_base), (
                    f"Expected the base-version response to contain NO emoji "
                    f"(formal tone), got: {response_base!r}"
                )
                assert "[TECH-STYLE]" not in response_base, (
                    f"Base-version response should NOT contain '[TECH-STYLE]', "
                    f"got: {response_base!r}"
                )
                chip_texts = agent_detail_page.get_last_message_tool_chip_texts(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert chip_texts == [f"Skill: {SKILL_NAME}"], (
                    f"Expected the last message's tool chip to read "
                    f"'Skill: {SKILL_NAME}' (autonomous invocation), got: {chip_texts!r}"
                )

            with allure.step("Side-channel check — no console errors across all 12 steps"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )

        finally:
            with allure.step("Cleanup — delete the Agent, then the Skill (removes all 3 versions)"):
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
