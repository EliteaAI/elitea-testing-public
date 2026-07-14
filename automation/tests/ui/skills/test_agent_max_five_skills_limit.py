"""Maximum 5 Skills can be attached to one Agent (ELITEA-1790).

Verifies that the platform enforces a maximum of 5 Skills per Agent: the
counter increments "0/5" -> "5/5" as Skills 1-5 are attached, and once 5/5
is reached the add-skill control becomes **disabled** (not merely rejecting
a 6th click) with an accessible tooltip explaining why — stronger
enforcement than the case text's own bar ("an error message *or* disabled
state"). Persistence across a full page reload is also confirmed (each
attach is auto-saved via API; there is no explicit agent-level Save for
this action).

No product defect found — the limit is enforced correctly and the
enforcement exceeds the case's own expectation.

Spec: test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md
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

logger = logging.getLogger("elitea.tests.skills")

SKILL_NAMES = [
    "elitea-1790-skill-2",
    "elitea-1790-skill-3",
    "elitea-1790-skill-4",
    "elitea-1790-skill-5",
    "elitea-1790-skill-6",
]
AGENT_NAME = "elitea-1790-max5skills-agent"


def _create_skill(page, name: str, instructions: str) -> int:
    """Create a skill via the UI and return its numeric ID.

    Mirrors the create flow shared across ELITEA-1735/1738/1739/1789: fill
    the form (name / description / CodeMirror instructions), save, and
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
        description=f"Test skill for ELITEA-1790 max-5-skills-per-agent verification — {name}.",
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


class TestAgentMaxFiveSkillsLimit:
    """Maximum 5 Skills can be attached to one Agent (ELITEA-1790, l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1790_maximum-5-skills-attached-to-one-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_max_five_skills_attach_limit(self, page, agent_api, skill_api):
        """Create 5 Skills + an Agent, attach all 5 Skills one at a time,
        verify the add-skill control disables at 5/5 with a tooltip (rather
        than a literal 6th-click rejection), and verify persistence via a
        full page reload.

        Steps (AFS test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md):
        1. Create 5 Skills via UI. A 6th distinct skill is looked up via the
           project's existing skills (via ``skill_api``) rather than assumed
           by name — any pre-existing skill satisfies the case's "6 distinct
           Skills" precondition.
        2. Create an Agent.
        3. Skills section starts at 0/5, add-skill control enabled.
        4-8. Attach Skills 1-5 one at a time; counter increments "N/5 skills
           added." and a card renders after each attach.
        9. Add-skill control becomes disabled the instant 5/5 is reached,
           with an accessible tooltip — a 6th skill cannot be attached.
        10. Confirm persistence via a full page reload (attach is
           auto-saved via API; no explicit agent-level Save is available).
        """
        skill_ids = []
        agent_id = None

        try:
            with allure.step("Step 1 — Create 5 Skills via UI"):
                for i, name in enumerate(SKILL_NAMES, start=2):
                    skill_id = _create_skill(
                        page,
                        name,
                        f"You are test skill {i} created for ELITEA-1790 "
                        f"verification. Respond with SKILL{i}.",
                    )
                    skill_ids.append(skill_id)
                assert len(skill_ids) == 5, (
                    f"Expected 5 freshly-created skills, got {len(skill_ids)}"
                )

            with allure.step(
                "Step 1b — Confirm a 6th distinct skill exists in the "
                "project (any pre-existing skill; not assumed by name)"
            ):
                # Exclude by id (this run's own 5 skills) AND by this test's
                # naming prefix — a same-named orphan left by a previously
                # interrupted run of this exact test (killed before its own
                # cleanup could run) would otherwise pass an id-only filter
                # and produce a false-positive is_skill_attached() match by
                # name later, since attachment verification is name-based,
                # not id-based. Confirmed live: an earlier interrupted run
                # left orphaned "elitea-1790-skill-*" skills in the project,
                # and an id-only filter picked one of them as the "6th"
                # skill, which then spuriously matched an attached same-named
                # skill from *this* run.
                all_skills = skill_api.list_skills().get("rows", [])
                sixth_skill = next(
                    (
                        s for s in all_skills
                        if s["id"] not in skill_ids
                        and not s.get("name", "").startswith("elitea-1790-skill-")
                    ),
                    None,
                )
                assert sixth_skill is not None, (
                    "A 6th distinct skill (not one of the 5 just created, "
                    "and not sharing this test's naming pattern) must exist "
                    "in the project to satisfy the case's precondition of "
                    "6 distinct Skills"
                )
                sixth_skill_name = sixth_skill["name"]

            with allure.step("Step 2 — Create an Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description=(
                        "Agent for ELITEA-1790 max-5-skills-per-agent verification."
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

            with allure.step(
                "Step 3 — Skills section starts at 0/5, add-skill control enabled"
            ):
                detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert "0/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 0 skills attached before attaching"
                )
                assert not detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "add-skill button should be enabled before any skills are attached"

            with allure.step("Steps 4-8 — Attach Skills 1-5 one at a time"):
                # Capture every skill-attach PATCH from here on, so the
                # blocked-6th-attach step below can assert on real network
                # traffic (no additional PATCH fires) rather than only UI
                # state — this is what the AFS Axis 2 row actually claims.
                attach_requests = detail_page.capture_requests_matching(
                    "skill/prompt_lib", method="PATCH"
                )
                for idx, name in enumerate(SKILL_NAMES, start=1):
                    detail_page.attach_skill(name, timeout=UI_ELEMENT_TIMEOUT)
                    counter = detail_page.get_skills_counter_text()
                    assert f"{idx}/5" in counter, (
                        f"Skills counter should show {idx}/5 after attaching "
                        f"skill #{idx} ('{name}'), got: {counter!r}"
                    )
                    assert detail_page.is_skill_attached(name), (
                        f"Skill card for '{name}' should render after attaching"
                    )
                    assert len(attach_requests) == idx, (
                        f"Expected exactly {idx} skill-attach PATCH request(s) "
                        f"after attaching skill #{idx}, captured: {attach_requests!r}"
                    )

            with allure.step(
                "Step 9 — Add-skill control becomes disabled at 5/5, with a "
                "tooltip explaining why (proactive disable, exceeding the "
                "case's own bar of 'error message OR disabled state')"
            ):
                assert detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "add-skill button should be disabled once 5/5 skills are attached"

                tooltip = detail_page.get_add_skill_button_tooltip(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert tooltip == "Maximum number of skills reached", (
                    "add-skill button's tooltip should explain the limit, "
                    f"got: {tooltip!r}"
                )

            with allure.step(
                "Step 9 (continued) — no 6th skill is attached; counter and "
                "attached-skill set remain unchanged; no additional "
                "skill-attach PATCH fires. Per the AFS, the control is "
                "genuinely disabled at the actionability level (a real "
                "Playwright click() would time out) — asserted via the "
                "disabled-state check above, not a literal click-and-"
                "expect-error. The 'no popper opens' claim in the AFS is "
                "NOT separately asserted here: the popper's only trigger is "
                "this same disabled button, so 'does the popper open' is "
                "untestable by construction once toBeDisabled() holds — see "
                "the AFS amendment note for this row."
            ):
                counter_before = detail_page.get_skills_counter_text()
                assert not detail_page.is_skill_attached(sixth_skill_name), (
                    f"Skill '{sixth_skill_name}' must not be attached — the "
                    "limit blocks a 6th attach before it can ever be attempted"
                )
                assert detail_page.get_skills_counter_text() == counter_before, (
                    "Skills counter must remain unchanged with the add-skill "
                    "control disabled"
                )
                # Real network-traffic assertion (not just UI state): exactly
                # the 5 PATCH requests from Steps 4-8 have fired — no 6th one,
                # for any skill id, appeared after reaching 5/5.
                assert len(attach_requests) == 5, (
                    "No additional skill-attach PATCH request should fire "
                    f"once the limit is reached, captured: {attach_requests!r}"
                )
                sixth_skill_id_suffix = f"/{sixth_skill['id']}"
                assert not any(
                    req["url"].endswith(sixth_skill_id_suffix) for req in attach_requests
                ), (
                    f"No PATCH request should ever target the 6th skill "
                    f"(id={sixth_skill['id']}), captured: {attach_requests!r}"
                )

            with allure.step(
                "Step 10 — Agent persists with exactly 5 Skills attached "
                "(auto-saved per-attach; confirmed via full page reload, "
                "no explicit agent-level Save is available for this action)"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                counter_after_reload = detail_page.wait_for_skills_counter(
                    "5/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "5/5" in counter_after_reload, (
                    "Skills counter should still show 5/5 after reload, "
                    f"got: {counter_after_reload!r}"
                )
                for name in SKILL_NAMES:
                    assert detail_page.is_skill_attached(name), (
                        f"Skill card for '{name}' should still render after reload"
                    )
                assert detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "add-skill button should still be disabled after reload"

        finally:
            # Cleanup per AFS: delete the agent first (teardown hygiene —
            # remove the thing with attached-state dependencies first), then
            # the 5 created skills, tolerating individual failures (mirrors
            # ELITEA-1735/1737/1738/1739/1789's cleanup pattern). The
            # pre-existing 6th skill is read-only reuse and is never deleted.
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            for skill_id in skill_ids:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                    )
