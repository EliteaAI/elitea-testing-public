"""`~` mention in Agent Instructions lists only currently attached Skills (ELITEA-1791).

Verifies that typing "~" in the Agent's Instructions field opens a "Mention
skill" suggestion panel scoped to ONLY the Agent's currently attached
Skills — an unattached Skill never appears, and the scoping is re-evaluated
live on every "~" trigger (not cached from the first invocation).

This is a distinct surface from the embedded-chat "~" mention flow already
covered by `test_skill_agent_interaction.py` / `test_skill_conversation_interaction.py`
(`AgentDetailPage.send_chat_message_with_mention`): both surface the same
"Mention skill" popper component, but target different input fields. See
`AgentDetailPage.type_tilde_in_instructions()` for the Instructions-field
entry point added for this case.

No product defect found — the mention-scoping behavior correctly matches
the case's Pass criteria exactly.

Spec: test-specs/skills/l3_tilde-mention-lists-only-attached-skills_ELITEA-1791.md
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

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

logger = logging.getLogger("elitea.tests.skills")

SKILL_A_NAME_IF_CREATED = "elitea-1791-skill-a"
SKILL_B_NAME = "elitea-1791-skill-b"
SKILL_C_NAME = "elitea-1791-skill-c"
AGENT_NAME = "elitea-1791-tilde-mention-agent"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1738/1739/1789/1790:
    fill the form (name / description / CodeMirror instructions), save, and
    confirm the nav-blocker dialog that fires on every save from the create
    form.
    """
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=name,
        instructions=instructions,
        description=(
            "Test skill for ELITEA-1791 tilde-mention-lists-only-attached-"
            f"skills verification — {name}."
        ),
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


class TestTildeMentionListsOnlyAttachedSkills:
    """`~` mention in Agent Instructions lists only currently attached Skills (ELITEA-1791, l3/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1791_tilde-mention-lists-only-attached-skills.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_tilde_mention_in_instructions_lists_only_attached_skills(
        self, page, agent_api, skill_api,
    ):
        """Attach 2 of 3 distinct Skills to an Agent, then verify the "~"
        mention panel in the Instructions field is scoped to only the
        attached 2 — the 3rd (unattached) Skill never appears, including
        on a second, independent "~" trigger after clearing the field.

        Steps (AFS test-specs/skills/l3_tilde-mention-lists-only-attached-skills_ELITEA-1791.md):
        1. Confirm/create 3 distinct Skills (reuse a pre-existing one as
           Skill A, looked up via API rather than assumed by name — same
           environment-robustness rule as ELITEA-1790's cleanup note —
           falling back to creating it fresh if none exists), create an
           Agent, attach Skill A + Skill B, leave Skill C unattached.
        2. Click the Instructions field — becomes focused/editable.
        3-4. Type "~" — "Mention skill" panel appears, listing exactly
           Skill A and Skill B; Skill C is asserted absent by exact-name
           locator (not merely a row count).
        5. Select Skill A — inserts "~<skill-name>" as plain text.
        6. Select-all + delete, retype "~" — same 2-item scoped list
           reappears; Skill C still absent (re-evaluated live).
        """
        skill_a_id = None
        skill_a_name = None
        skill_a_created = False
        skill_b_id = None
        skill_c_id = None
        agent_id = None

        try:
            with allure.step(
                "Step 1a — Confirm/create 3 distinct Skills: reuse a "
                "pre-existing skill as Skill A (looked up via API rather "
                "than assumed by name — its name is environment-specific "
                "test data, not a guaranteed fixture), create Skill B and "
                "Skill C fresh"
            ):
                existing_skills = skill_api.list_skills().get("rows", [])
                reusable = next(
                    (
                        s for s in existing_skills
                        if not s.get("name", "").startswith("elitea-1791-")
                    ),
                    None,
                )
                if reusable is not None:
                    skill_a_id = reusable["id"]
                    skill_a_name = reusable["name"]
                    logger.info(
                        "Reusing pre-existing skill as Skill A: id=%s name=%r",
                        skill_a_id, skill_a_name,
                    )
                else:
                    skill_a_name = SKILL_A_NAME_IF_CREATED
                    skill_a_id = _create_skill(
                        page, skill_a_name,
                        "You are test skill A created for ELITEA-1791 verification.",
                    )
                    skill_a_created = True

                skill_b_id = _create_skill(
                    page, SKILL_B_NAME,
                    "You are test skill B created for ELITEA-1791 verification.",
                )
                skill_c_id = _create_skill(
                    page, SKILL_C_NAME,
                    "You are test skill C created for ELITEA-1791 verification.",
                )
                assert len({skill_a_id, skill_b_id, skill_c_id}) == 3, (
                    "Skills A, B, C must be 3 distinct skill ids, got "
                    f"A={skill_a_id}, B={skill_b_id}, C={skill_c_id}"
                )

            with allure.step(
                "Step 1b — Create Agent, attach Skill A and Skill B, leave "
                "Skill C unattached"
            ):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description=(
                        "Agent for ELITEA-1791 tilde-mention-lists-only-"
                        "attached-skills verification."
                    ),
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

                detail_page.attach_skill(skill_a_name, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching Skill A"
                )
                detail_page.attach_skill(SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "2/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 2 skills attached after attaching Skill B"
                )
                assert detail_page.is_skill_attached(skill_a_name), (
                    f"Skill card for Skill A ('{skill_a_name}') should render after attaching"
                )
                assert detail_page.is_skill_attached(SKILL_B_NAME), (
                    f"Skill card for Skill B ('{SKILL_B_NAME}') should render after attaching"
                )
                assert not detail_page.is_skill_attached(SKILL_C_NAME), (
                    f"Skill C ('{SKILL_C_NAME}') must NOT be attached to the "
                    "agent — it is this case's negative-control skill"
                )

            with allure.step(
                "Step 2 — Navigate to the Agent Instructions field "
                "(case-text drift resolved: this is the Instructions "
                "accordion textarea, not the embedded-chat input — see AFS "
                "Metadata clarification)"
            ):
                detail_page.instructions_input.click()
                expect(detail_page.instructions_input).to_be_focused()

            with allure.step(
                "Steps 3-4 — Typing '~' opens the 'Mention skill' panel "
                "scoped to ONLY the 2 attached skills; Skill C never appears"
            ):
                # Capture attached-skills traffic from this point forward —
                # confirms the mention list is a client-side filter with no
                # additional fetch on '~' (AFS Network Behavior / Axis 2).
                skills_requests = detail_page.capture_requests_matching(
                    "application_skills", method="GET"
                )

                # Console-error capture scoped to the actual '~' trigger
                # interactions under test (this step's trigger + step 6's
                # re-trigger below) — established pattern
                # (test_agent_max_five_skills_limit.py / test_skill_tag_filter.py):
                # page.on("console", ...), collect type == "error", assert
                # empty. Registered here (not before setup) so incidental
                # console noise from skill/agent creation and attach can't
                # fail an assertion that's about mention-trigger scoping.
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                detail_page.type_tilde_in_instructions(timeout=UI_ELEMENT_TIMEOUT)

                assert not skills_requests, (
                    "No network request should fire when typing '~' in the "
                    "Instructions field — the mention list is a client-side "
                    f"filter over already-fetched data, captured: {skills_requests!r}"
                )

                expect(
                    detail_page.get_instructions_mention_item(
                        skill_a_name, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(1)
                expect(
                    detail_page.get_instructions_mention_item(
                        SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(1)
                # Strong negative assertion (not merely a row count): the
                # unattached Skill C's exact name must not appear ANYWHERE
                # in the panel — a count assertion alone wouldn't catch it
                # leaking under a different label.
                expect(
                    detail_page.get_instructions_mention_item(
                        SKILL_C_NAME, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(0)

                assert not console_messages, (
                    "Expected no console errors after the first '~' trigger, "
                    f"got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 5 — Select Skill A from the suggestions inserts "
                "'~<skill-name>' as plain text into the Instructions field"
            ):
                detail_page.select_skill_from_instructions_mention(
                    skill_a_name, timeout=UI_ELEMENT_TIMEOUT,
                )
                inserted_text = detail_page.get_instructions()
                # Live product appends a trailing space after the inserted
                # mention (so typing can continue immediately) — confirmed
                # during implementer exploration, not a defect; strip it
                # before comparing so the assertion targets the actual
                # inserted content, not incidental trailing whitespace.
                assert inserted_text.strip() == f"~{skill_a_name}", (
                    "Instructions field should contain the inserted mention "
                    f"as plain text, got: {inserted_text!r}"
                )

            with allure.step(
                "Step 6 — Select-all + delete, retype '~': suggestion list "
                "reappears scoped to the same 2 attached skills; Skill C "
                "still absent (re-evaluated live on every trigger, not "
                "cached from the first invocation)"
            ):
                detail_page.clear_instructions_field()
                assert detail_page.get_instructions() == "", (
                    "Instructions field should be empty after select-all + delete"
                )

                detail_page.type_tilde_in_instructions(timeout=UI_ELEMENT_TIMEOUT)

                expect(
                    detail_page.get_instructions_mention_item(
                        skill_a_name, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(1)
                expect(
                    detail_page.get_instructions_mention_item(
                        SKILL_B_NAME, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(1)
                expect(
                    detail_page.get_instructions_mention_item(
                        SKILL_C_NAME, timeout=UI_ELEMENT_TIMEOUT,
                    )
                ).to_have_count(0)

                assert not console_messages, (
                    "Expected no console errors after the second '~' trigger, "
                    f"got: {[m.text for m in console_messages]}"
                )

        finally:
            # Cleanup per AFS: delete the agent first (teardown hygiene —
            # remove the thing with attached-state dependencies first), then
            # the created skills, tolerating individual failures (mirrors
            # ELITEA-1735/1737/1738/1739/1789/1790's cleanup pattern). The
            # reused pre-existing skill (if any) is read-only and never deleted.
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)

            created_skill_ids = [skill_b_id, skill_c_id]
            if skill_a_created:
                created_skill_ids.append(skill_a_id)
            for skill_id in created_skill_ids:
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%d", skill_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                        )
