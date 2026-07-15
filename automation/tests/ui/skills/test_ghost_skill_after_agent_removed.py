"""Ghost skill not shown after Agent participant removed (ELITEA-1793).

Verifies that adding an agent as a chat participant surfaces its attached
skill via "~mention", that dismissing the mention popper and removing the
participant both work cleanly — and (per a known, deterministic product
defect) that re-typing "~" after removal should NOT surface the removed
agent's skill again.

Steps 1-4 (add participant, confirm mention shows the skill, dismiss,
remove participant) are hard-asserted: no product defect there. Steps 5-6
(re-check "~mention" post-removal) are soft-asserted — the removed agent's
skill ghosts in the "Mention skill" popper, a genuine, deterministically
reproducible (2/2) product defect, filed as
github.com/EliteaAI/elitea-testing-public/issues/51. Soft-asserting means
this test goes red the instant #51 is fixed, without masking the defect or
blocking the rest of the flow.

No conversation is ever created in this case (the message is never sent),
so cleanup only needs to remove the agent + skill.

Spec: test-specs/skills/l3_ghost-skill-not-shown-after-agent-participant-removed_ELITEA-1793.md
"""

import logging

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

logger = logging.getLogger("elitea.tests.skills")

SKILL_NAME = "elitea-1793-ghost-skill"
SKILL_DESCRIPTION = "ELITEA-1793 automation skill — ghost-skill-after-remove verification."
SKILL_INSTRUCTIONS = "Tell jokes about robots. Always output in UPPER CASE"
AGENT_NAME = "elitea-1793-joker-agent"

KNOWN_DEFECT_ISSUE = "github.com/EliteaAI/elitea-testing-public/issues/51"


def _create_skill(page, name: str, description: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1736/1737/1789/1792.
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


class TestGhostSkillAfterAgentRemoved:
    """Ghost skill not shown after Agent participant removed (ELITEA-1793, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1793_ghost-skill-not-shown-after-agent-participant-removed.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(KNOWN_DEFECT_ISSUE, "Known defect — ghost skill in mention popper")
    @pytest.mark.p3
    @pytest.mark.regression
    def test_ghost_skill_not_shown_after_agent_participant_removed(
        self, page, agent_api, skill_api,
    ):
        """Create a skill, attach it to an agent, add the agent as a chat
        participant, confirm '~mention' shows the skill, dismiss, remove the
        participant, and (soft-asserted, known defect) confirm the skill no
        longer appears in '~mention' afterward.

        Steps (AFS test-specs/skills/l3_ghost-skill-not-shown-after-agent-participant-removed_ELITEA-1793.md):
        1. Create Skill, create Agent, attach the skill to the agent.
        2. Open Chat, add the agent as a participant.
        3. Type '~' — the "Mention skill" popper lists the attached skill.
        4. Dismiss the popper with Escape without selecting anything.
        5. Remove the agent from the chat's participants.
        6. Type '~' again — soft-asserted per known defect #51: the removed
           agent's skill should NOT be listed, but live product still shows
           it (ghost).
        7. Control check: a fresh conversation that never had a participant
           shows the correct "No skills attached to this agent" empty state
           — proving the ghost is specifically a stale-state-after-removal
           bug, not "the mention list always shows all project skills".
        """
        skill_id = None
        agent_id = None
        soft_failures = []

        try:
            with allure.step("Step 1 — Create Skill and Agent, attach the skill to the agent"):
                skill_id = _create_skill(
                    page, SKILL_NAME, SKILL_DESCRIPTION, SKILL_INSTRUCTIONS,
                )

                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description="ELITEA-1793 automation agent — ghost-skill-after-remove verification.",
                    instructions="Entertain the user with jokes",
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

                detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for '{SKILL_NAME}' should render after attaching"
                )

            with allure.step("Step 2 — Open Chat and add the Agent as a participant"):
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
                assert chat.is_participants_badge_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "'Agents in this conversation' badge should be present "
                    "with 1 participant added"
                )

            with allure.step(
                "Step 3 — Type '~': the 'Mention skill' popper lists the "
                "attached skill by name and description"
            ):
                popper = chat.open_mention_skill_popper(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_skill_in_mention_popper(
                    popper, SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"'Mention skill' popper should list '{SKILL_NAME}' while "
                    "its agent is still an active participant"
                )
                assert chat.is_skill_in_mention_popper(
                    popper, SKILL_DESCRIPTION, timeout=2000
                ), (
                    "'Mention skill' popper should show the skill's "
                    "description text alongside its name"
                )

            with allure.step(
                "Step 4 — Dismiss the popper with Escape without selecting anything"
            ):
                chat.dismiss_mention_popper()
                assert not chat.is_mention_popper_open(timeout=2000), (
                    "'Mention skill' popper should be closed after Escape"
                )

            with allure.step("Step 5 — Remove the agent from the chat's participants"):
                chat.remove_agent_participant(agent_id, timeout=UI_ELEMENT_TIMEOUT)

                assert not chat.is_switch_agent_button_visible(timeout=3000), (
                    "Composer should no longer show the 'Switch Agent' "
                    "button (i.e. no active agent participant) after removal"
                )
                assert not chat.is_participants_badge_visible(timeout=3000), (
                    "'Agents in this conversation' badge should disappear "
                    "entirely from the DOM at 0 participants (not show '0')"
                )

            with allure.step(
                "Step 6 — Type '~' again (soft-assert, known defect "
                f"{KNOWN_DEFECT_ISSUE}): the removed agent's skill should "
                "NOT be listed"
            ):
                popper_after_removal = chat.open_mention_skill_popper(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                ghost_skill_shown = chat.is_skill_in_mention_popper(
                    popper_after_removal, SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                # Known defect: github.com/EliteaAI/elitea-testing-public/issues/51 —
                # the "Mention skill" popper retains the removed agent's
                # skill (a stale client-side list that isn't invalidated on
                # participant-remove). Soft-assert (record, don't raise) so
                # the control check in Step 7 still runs and reports; this
                # test goes red the moment #51 is fixed.
                if ghost_skill_shown:
                    logger.warning(
                        "Known defect #51 reproduced: '%s' still listed in "
                        "'Mention skill' popper after its agent was removed",
                        SKILL_NAME,
                    )
                    soft_failures.append(
                        f"Known defect {KNOWN_DEFECT_ISSUE}: skill '{SKILL_NAME}' "
                        "still appears in the 'Mention skill' popper after its "
                        "participant agent was removed from the chat"
                    )
                chat.dismiss_mention_popper()

            with allure.step(
                "Step 7 — Control check: a fresh conversation (no participant "
                "ever added) shows the correct 'No skills attached to this "
                "agent' empty state — proves the ghost is specifically a "
                "stale-state-after-removal bug"
            ):
                new_tab = page.context.new_page()
                try:
                    fresh_chat = ChatPage(new_tab)
                    fresh_chat.navigate_to_chat()
                    fresh_popper = fresh_chat.open_mention_skill_popper(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    assert fresh_chat.is_mention_popper_empty_state(
                        fresh_popper, timeout=UI_ELEMENT_TIMEOUT
                    ), (
                        "A fresh conversation with no participant ever added "
                        "should show the 'No skills attached to this agent' "
                        "empty state in the 'Mention skill' popper"
                    )
                    assert not fresh_chat.is_skill_in_mention_popper(
                        fresh_popper, SKILL_NAME, timeout=2000
                    ), (
                        f"A fresh conversation should NOT list '{SKILL_NAME}' "
                        "— ruling out 'the mention list always shows all "
                        "project skills' as an alternative explanation"
                    )
                finally:
                    new_tab.close()

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known deterministic product "
                    "defect, not test/infrastructure — rest of the flow "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: no conversation is ever created in this case
            # (the message is never sent), so only the agent and skill need
            # tearing down — mirrors ELITEA-1735/1736/1789/1792's pattern.
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            if skill_id is not None:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                    )
