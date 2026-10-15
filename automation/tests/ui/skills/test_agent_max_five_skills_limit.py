"""Maximum Skills that can be attached to one Agent (ELITEA-1790).

Verifies that the platform enforces a maximum number of Skills per Agent,
read LIVE from the API's ``application_skills.max_skills`` field rather than
a hardcoded literal: the counter increments "0/{max_skills}" ->
"{max_skills}/{max_skills}" as Skills are attached, and once the limit is
reached the add-skill control becomes **disabled** (not merely rejecting a
click) with an accessible tooltip explaining why — stronger enforcement than
the case text's own bar ("an error message *or* disabled state"). Persistence
across a full page reload is also confirmed (each attach is auto-saved via
API; there is no explicit agent-level Save for this action).

No product defect found — the limit is enforced correctly and the
enforcement exceeds the case's own expectation.

**2026-10-15 adjustment (issue #2443):** EL-6930 (EliteaUI commit
``8a1ae6b9``, 2026-10-13) moved the per-Agent Skill cap from a
frontend-hardcoded ``5`` to the API's own ``max_skills`` field, which
currently serves ``50`` on DEV. ``max_skills`` is confirmed NOT configurable
anywhere (no project-settings control, no OpenAPI write path, pure
server-side global) — live-verified during this adjustment, so attaching the
limit's worth of Skills one at a time through the UI would be both
unavailable-by-design and bad test design (dozens of UI round-trips with no
additional proof over a handful). The fix: read ``max_skills`` live once,
bulk-attach everything below the boundary via the API (``skill_api``'s new
``attach_skill_to_agent``/``get_application_skills`` methods — a declared
TRANSIT substitution, see the AFS's Fidelity Declaration), and keep the
boundary-crossing attach and the over-limit attempt on the real UI, exactly
as before. The test never hardcodes ``5`` or ``50`` — if the platform's
limit moves again, this test keeps working without another adjustment round.

The test OWNS its precondition: it creates every distinct Skill the case
calls for (``max_skills`` to attach + one that is never attached), under
run-unique names, and reads nothing out of whatever data happens to
pre-exist in the target project (issue #1811, 2026-08-27 adjustment).

Spec: test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md
"""

import logging
from uuid import uuid4

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

# How many Skills are created through the real UI create form, independent
# of the live max_skills value — enough to prove the create flow still
# works (matching the case's original "create N distinct Skills" framing)
# without turning setup into dozens of UI round-trips. One (created first)
# is never attached; the other (created LAST, after the bulk-API batch —
# see the attach_skill() docstring gotcha) is the boundary-crossing attach
# target.
UI_CREATED_SKILL_COUNT = 2
AGENT_NAME = "elitea-1790-max5skills-agent"


def _run_unique_skill_names(count: int) -> list[str]:
    """Return ``count`` run-unique skill names, e.g. ``el1790-3f9a2c11-s1``.

    Run-uniqueness is REQUIRED, not cosmetic: both the attach-popper
    selection and ``AgentDetailPage.is_skill_attached()`` match skills by
    NAME. With fixed names, a hard-killed run (whose ``finally`` cleanup
    never ran) leaves same-named orphans behind, the popper then lists two
    rows with the same name, and a name-based match silently reads a
    stranger's entity — a false positive that no assertion can catch.

    Shape obeys the skill-name validation the create form enforces:
    lowercase letters / digits / hyphens only, no leading or trailing
    hyphen, at most 64 characters — ``SKILL_NAME_MAX_LENGTH`` and
    ``SKILL_NAME_RE`` in EliteaUI
    ``src/[fsd]/features/skill/lib/validation/skillValidationSchema.validation.js``
    (verified on ``origin/main``), which mirrors the backend's
    ``validate_skill_name``. Comfortably inside the limit even at the
    current ``max_skills=50`` (count=51 -> names up to 20 chars).
    """
    run_id = uuid4().hex[:8]
    return [f"el1790-{run_id}-s{n}" for n in range(1, count + 1)]


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
        description=f"Test skill for ELITEA-1790 max-skills-per-agent verification — {name}.",
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
    """Maximum Skills can be attached to one Agent (ELITEA-1790, l2/p1).

    Name kept stable across the 2026-10-15 adjustment (EL-6930: the limit
    moved from a hardcoded 5 to a live API field) for ``automation_test_id``
    continuity — the file/class/function name is implementation history, not
    an observable this case asserts.
    """

    @pytest.mark.tms("ELITEA-1790")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-1790_maximum-5-skills-attached-to-one-agent.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_max_five_skills_attach_limit(self, page, agent_api, skill_api):
        """Create an Agent, read the live per-Agent Skill limit, create and
        attach that many Skills (bulk-attaching everything below the
        boundary via the API, the boundary-crossing attach via the real
        UI), verify the add-skill control disables at the limit with a
        tooltip, and verify persistence via a full page reload.

        Steps (AFS test-specs/skills/lp1_max-5-skills-per-agent_ELITEA-1790.md,
        § Adjustment — 2026-10-15):
        1. Create the never-attached Skill via the UI — proves the create
           flow still works (this case's original "create N distinct
           Skills" framing).
        2. Create an Agent.
        2b. Read the live per-Agent Skill limit (``max_skills``) from the
            ``application_skills`` API, right after the Agent exists and
            before any attach. Never hardcoded.
        3. Skills section starts at 0/{max_skills}, add-skill control
           enabled.
        4. Create the bulk-attach Skills (``max_skills - 1``, via the API —
           setup, not the observable).
        5. Bulk-attach them via the API (declared transit substitution —
           the case's observable, the control disabling at the real limit,
           is produced by the product's own count and is read at steps
           7/8 below, both still real-UI).
        6. Create the boundary Skill via the UI, LAST — the single
           most-recently-created Skill in the project at this point, which
           is what keeps it reachable through the real "+ Skill" popper
           (see the gotcha note below). Then confirm all
           ``max_skills + 1`` created Skills read back from the project
           (the case's "N distinct Skills exist" precondition).
        7. Attach the boundary Skill through the real UI — the one attach
           whose result this case actually verifies — reaching
           {max_skills}/{max_skills}.
        8. Add-skill control becomes disabled the instant the limit is
           reached, with an accessible tooltip.
        8 (continued). Attempt to attach the never-attached Skill —
           blocked before any request fires.
        9. Confirm persistence via a full page reload (attach is
           auto-saved via API; no explicit agent-level Save is available).

        **Automation gotcha (live-confirmed during this adjustment, issue
        #2443):** the "+ Skill" popper's item list (`SkillMenu.jsx` ->
        `useSkillListQuery`) is unfiltered/unsearched here and is
        server-sorted `created_at desc` at a fixed `PAGE_SIZE=20`
        (`skillsApi.js`), excluding already-attached skills. A Skill
        created *before* the bulk-attach-via-API batch falls off page 1 and
        is unreachable through `AgentDetailPage.attach_skill()`'s
        `.filter(has_text=...)` — confirmed by a first attempt that created
        the boundary Skill before the bulk batch and timed out locating it
        in the popper. Creating it LAST (step 6, after the bulk batch)
        keeps it the single most-recent Skill in the project, which is what
        makes it reachable regardless of how large `max_skills` is.
        """
        agent_id = None
        agent_version_id = None
        max_skills = None
        created_skill_ids = []  # every Skill this run creates — the cleanup set
        bulk_attach_skills = []  # [{"id": int, "version_id": int, "name": str}, ...]
        boundary_skill_id = None
        boundary_skill_name = None
        overlimit_skill_id = None
        overlimit_skill_name = None
        attach_requests = None  # CapturedRequests, needs stop() in finally
        console_messages = None  # CapturedConsoleMessages, needs stop() in finally

        try:
            with allure.step(
                "Step 1 — Create the never-attached Skill via the UI "
                "(proves the create flow still works)"
            ):
                ui_skill_names = _run_unique_skill_names(UI_CREATED_SKILL_COUNT)
                overlimit_skill_name, boundary_skill_name = ui_skill_names
                overlimit_skill_id = _create_skill(
                    page,
                    overlimit_skill_name,
                    "You are the never-attached test skill created for "
                    "ELITEA-1790 verification. Respond with OVERLIMIT.",
                )
                created_skill_ids.append(overlimit_skill_id)

            with allure.step("Step 2 — Create an Agent"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME,
                    description=(
                        "Agent for ELITEA-1790 max-skills-per-agent verification."
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
                agent_version_id = int(detail_page.get_version_id())
                logger.info(
                    "Created agent %r with id=%d, version_id=%d",
                    AGENT_NAME, agent_id, agent_version_id,
                )

            with allure.step(
                "Step 2b — Read the live per-Agent Skill limit (max_skills) "
                "from the application_skills API, before any attach"
            ):
                application_skills = skill_api.get_application_skills(agent_version_id)
                max_skills = application_skills.get("max_skills")
                assert isinstance(max_skills, int) and max_skills > 0, (
                    "application_skills.max_skills should be a positive int, "
                    f"got: {application_skills!r}"
                )
                assert application_skills.get("skills") == [], (
                    "A freshly-created Agent should have no Skills attached yet, "
                    f"got: {application_skills!r}"
                )
                logger.info("Live per-Agent Skill limit: max_skills=%d", max_skills)

            with allure.step(
                "Step 3 — Skills section starts at 0/{max_skills}, "
                "add-skill control enabled"
            ):
                detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert "0/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should show 0 skills attached before attaching"
                )
                assert not detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "add-skill button should be enabled before any skills are attached"

            with allure.step(
                "Step 4 — Create the bulk-attach Skills via the API "
                "(max_skills - 1 of them — setup for the precondition, not "
                "the observable)"
            ):
                bulk_count = max_skills - 1
                bulk_skill_names = _run_unique_skill_names(bulk_count) if bulk_count > 0 else []
                for name in bulk_skill_names:
                    skill = skill_api.create_skill(
                        name=name,
                        description=(
                            f"Test skill for ELITEA-1790 max-skills-per-agent "
                            f"verification — {name}."
                        ),
                        instructions=(
                            f"You are a bulk-attach test skill ({name}) created "
                            "for ELITEA-1790 verification. Respond with BULK."
                        ),
                    )
                    skill_version_id = skill["versions"][0]["id"]
                    bulk_attach_skills.append(
                        {"id": skill["id"], "version_id": skill_version_id, "name": name}
                    )
                    created_skill_ids.append(skill["id"])
                logger.info(
                    "Created %d Skills via the API for bulk-attach", len(bulk_attach_skills)
                )

            with allure.step(
                "Step 5 — Bulk-attach max_skills - 1 Skills via the API "
                "(declared transit substitution — reaching the precondition, "
                "not the observable; the boundary attach and the over-limit "
                "attempt below both stay real-UI)"
            ):
                for skill in bulk_attach_skills:
                    skill_api.attach_skill_to_agent(
                        agent_version_id=agent_version_id,
                        skill_id=skill["id"],
                        skill_version_id=skill["version_id"],
                    )
                # Ground-truth verification via the API's own read-back —
                # the equivalent, for an API-driven setup phase, of the
                # per-attach network-count assertions the real-UI steps use.
                application_skills_after_bulk = skill_api.get_application_skills(
                    agent_version_id
                )
                attached_ids_after_bulk = {
                    s["skill_id"] for s in application_skills_after_bulk.get("skills", [])
                }
                expected_bulk_ids = {s["id"] for s in bulk_attach_skills}
                assert attached_ids_after_bulk == expected_bulk_ids, (
                    f"Expected exactly the bulk-attached skill ids to be attached "
                    f"after Step 5, got: {attached_ids_after_bulk!r} vs expected "
                    f"{expected_bulk_ids!r}"
                )

                # The UI's RTK Query cache doesn't know about API-driven
                # attaches until it refetches — reload once to observe the
                # real count before the boundary attach (mirrors the
                # pre-adjustment test's "4/5, limit not yet engaged"
                # checkpoint, generalized to the dynamic limit).
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                counter_after_bulk = detail_page.wait_for_skills_counter(
                    f"{bulk_count}/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert f"{bulk_count}/{max_skills}" in counter_after_bulk, (
                    f"Skills counter should show {bulk_count}/{max_skills} after "
                    f"the bulk attach, got: {counter_after_bulk!r}"
                )
                assert not detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "add-skill button should still be enabled with "
                    f"{bulk_count}/{max_skills} attached — the limit has not "
                    "yet engaged"
                )

            with allure.step(
                "Step 6 — Create the boundary Skill via the UI, LAST (it "
                "must be the single most-recently-created Skill in the "
                "project to stay reachable through the unfiltered '+ Skill' "
                "popper — see the automation gotcha in this test's "
                "docstring), then confirm all max_skills + 1 created Skills "
                "read back from the project (the case's 'N distinct Skills "
                "exist' precondition)"
            ):
                boundary_skill_id = _create_skill(
                    page,
                    boundary_skill_name,
                    "You are the boundary-crossing test skill created for "
                    "ELITEA-1790 verification. Respond with BOUNDARY.",
                )
                created_skill_ids.append(boundary_skill_id)

                expected_total = max_skills + 1
                assert len(set(created_skill_ids)) == expected_total, (
                    f"Expected {expected_total} distinct freshly-created skill "
                    f"ids, got: {created_skill_ids!r}"
                )
                project_skill_ids = {
                    s["id"] for s in skill_api.list_skills(limit=500).get("rows", [])
                }
                missing_skill_ids = [
                    sid for sid in created_skill_ids if sid not in project_skill_ids
                ]
                assert not missing_skill_ids, (
                    f"All {expected_total} created Skills must be present in the "
                    f"project to satisfy the case's precondition; missing ids: "
                    f"{missing_skill_ids!r}"
                )

                # _create_skill() left the browser on the new skill's detail
                # page — return to the agent before attaching.
                detail_page.navigate(agent_id)

            with allure.step(
                "Step 7 — Attach the boundary Skill through the real UI — "
                "the one attach whose result this case actually verifies"
            ):
                attach_requests = detail_page.capture_requests_matching(
                    "skill/prompt_lib", method="PATCH"
                )
                console_messages = detail_page.capture_console_errors()

                detail_page.attach_skill(boundary_skill_name, timeout=UI_ELEMENT_TIMEOUT)
                counter_after_boundary = detail_page.get_skills_counter_text()
                assert f"{max_skills}/{max_skills}" in counter_after_boundary, (
                    f"Skills counter should show {max_skills}/{max_skills} after "
                    f"the boundary attach, got: {counter_after_boundary!r}"
                )
                assert detail_page.is_skill_attached(boundary_skill_name), (
                    f"Skill card for '{boundary_skill_name}' should render after "
                    "the boundary attach"
                )
                assert len(attach_requests) == 1, (
                    "Expected exactly 1 skill-attach PATCH request for the "
                    f"boundary attach, captured: {attach_requests!r}"
                )
                assert attach_requests[-1]["status"] == 201, (
                    "The boundary attach's PATCH should return 201, captured: "
                    f"{attach_requests[-1]!r}"
                )
                assert not console_messages, (
                    "Expected no console errors after the boundary attach, "
                    f"got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 8 — Add-skill control becomes disabled at "
                "{max_skills}/{max_skills}, with a tooltip explaining why "
                "(proactive disable, exceeding the case's own bar of "
                "'error message OR disabled state')"
            ):
                assert detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "add-skill button should be disabled once "
                    f"{max_skills}/{max_skills} skills are attached"
                )

                tooltip = detail_page.get_add_skill_button_tooltip(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert tooltip == "Maximum number of skills reached", (
                    "add-skill button's tooltip should explain the limit, "
                    f"got: {tooltip!r}"
                )

            with allure.step(
                "Step 8 (continued) — the never-attached skill is not "
                "attached; counter and attached-skill set remain unchanged; "
                "no additional skill-attach PATCH fires. The control is "
                "genuinely disabled at the actionability level (a real "
                "Playwright click() would time out) — asserted via the "
                "disabled-state check above, not a literal click-and-"
                "expect-error."
            ):
                counter_before = detail_page.get_skills_counter_text()
                assert not detail_page.is_skill_attached(overlimit_skill_name), (
                    f"Skill '{overlimit_skill_name}' must not be attached — the "
                    "limit blocks the attach before it can ever be attempted"
                )
                assert detail_page.get_skills_counter_text() == counter_before, (
                    "Skills counter must remain unchanged with the add-skill "
                    "control disabled"
                )
                # Real network-traffic assertion (not just UI state): no
                # additional PATCH fired beyond the single boundary attach
                # from Step 7, for any skill id.
                assert len(attach_requests) == 1, (
                    "No additional skill-attach PATCH request should fire "
                    f"once the limit is reached, captured: {attach_requests!r}"
                )
                overlimit_skill_id_suffix = f"/{overlimit_skill_id}"
                assert not any(
                    req["url"].endswith(overlimit_skill_id_suffix)
                    for req in attach_requests
                ), (
                    "No PATCH request should ever target the never-attached "
                    f"skill (id={overlimit_skill_id}), captured: {attach_requests!r}"
                )
                assert not console_messages, (
                    "Expected no console errors after the blocked attach "
                    f"attempt, got: {[m.text for m in console_messages]}"
                )

            with allure.step(
                "Step 9 — Agent persists with exactly max_skills Skills "
                "attached (auto-saved per-attach; confirmed via full page "
                "reload, no explicit agent-level Save is available for "
                "this action)"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                counter_after_reload = detail_page.wait_for_skills_counter(
                    f"{max_skills}/", timeout=UI_ELEMENT_TIMEOUT,
                )
                assert f"{max_skills}/{max_skills}" in counter_after_reload, (
                    f"Skills counter should still show {max_skills}/{max_skills} "
                    f"after reload, got: {counter_after_reload!r}"
                )
                assert detail_page.is_skill_attached(boundary_skill_name), (
                    f"Skill card for '{boundary_skill_name}' should still "
                    "render after reload"
                )
                for skill in bulk_attach_skills:
                    assert detail_page.is_skill_attached(skill["name"]), (
                        f"Skill card for '{skill['name']}' should still render "
                        "after reload"
                    )
                assert detail_page.is_add_skill_button_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), "add-skill button should still be disabled after reload"
                assert not console_messages, (
                    "Expected no console errors after the full page reload, "
                    f"got: {[m.text for m in console_messages]}"
                )

        finally:
            # Stop listeners to prevent resource leaks that cause test hangs.
            if attach_requests is not None:
                attach_requests.stop()
            if console_messages is not None:
                console_messages.stop()

            # Cleanup per AFS: delete the agent first (teardown hygiene —
            # remove the thing with attached-state dependencies first), then
            # every created skill, tolerating individual failures (mirrors
            # ELITEA-1735/1737/1738/1739/1789's cleanup pattern). The test
            # deletes only data it created; pre-existing project data is
            # never touched.
            if agent_id is not None:
                try:
                    agent_api.delete_agent(agent_id)
                    logger.info("Cleanup: deleted agent id=%d", agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete agent id=%s: %s", agent_id, exc
                    )
            for skill_id in created_skill_ids:
                try:
                    skill_api.delete_skill(skill_id)
                    logger.info("Cleanup: deleted skill id=%d", skill_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete skill id=%s: %s", skill_id, exc
                    )

        # Cleanup verification — only reached if the flow above didn't raise
        # (an exception in the try block propagates past `finally`, so this
        # never runs on top of an already-failed test and can't mask it).
        # Confirms every created skill and the agent are actually gone, not
        # just that the delete calls didn't raise.
        with allure.step(
            "Cleanup verification — this run's created skills and the "
            "Agent are gone"
        ):
            remaining_skill_ids = {
                s["id"] for s in skill_api.list_skills(limit=500).get("rows", [])
            }
            leaked_skill_ids = set(created_skill_ids) & remaining_skill_ids
            assert not leaked_skill_ids, (
                f"Cleanup should have deleted all {len(created_skill_ids)} "
                f"created skills; still present: {leaked_skill_ids!r}"
            )
            remaining_agent_ids = {
                a["id"] for a in agent_api.list_agents().get("rows", [])
            }
            assert agent_id not in remaining_agent_ids, (
                f"Cleanup should have deleted agent id={agent_id}; it is "
                "still present in the agents list"
            )
