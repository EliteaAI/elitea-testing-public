"""Agent with Skills — Validation Attribution and Token Invalidation (ELITEA-2601).

Part A — validation findings on an agent's attached skills are attributed to
    the correct skill BY NAME (``context: "skill: <name>"``), independently
    for each Critical rule a skill's content trips (too-short AND
    placeholder-text are separate, independently-attributed checks — a
    skill deliberately failing both produces TWO ``critical_issues[]``
    entries, not one combined message). A valid skill attached to the same
    agent shows zero Critical/Warning entries. Removing the invalid skill
    and re-validating clears the Critical issues and enables Publish.

Part B — a ``validation_token``-bearing wizard held open in one browser tab
    is invalidated by a skill change (attach OR remove) made to the SAME
    agent version in a second tab — confirmed via a real ``400
    validation_failed`` response with an exact, inline-rendered error
    message. The wizard does not auto-recover; the user must Cancel and
    restart Preparation -> Validation from scratch. This dispatch live-
    verifies BOTH directions (addition AND removal) — the AFS's own live
    run only confirmed the addition direction (a test-data confound left
    the removal direction unconfirmed; see AFS § Blocked Steps), so a
    dedicated, separately-valid ``extra-skill`` is seeded here specifically
    to let the removal direction run clean, and this test's own green run
    IS that live verification.

New ``AgentDetailPage`` methods added this dispatch (additive-only,
mirroring ``SkillDetailPage``'s existing ELITEA-2597 shapes for the same
shared ``PublishWizardModal.jsx`` component — see each method's docstring
for why it's a new sibling rather than a change to an existing, callers-
bearing method): ``click_publish_continue_and_capture_response()``,
``is_publish_confirm_enabled()``, ``confirm_publish_and_capture_response()``,
``get_publish_error_message()``, ``close_publish_wizard()``,
``navigate_to_configuration_tab()``. No new testids — every locator used
(including ``publish-wizard-error-alert``) already exists on
``automation/testids``.

Test case: ELITEA-2601
AFS: test-specs/skills/l2_agent-with-skills-validation-attribution-and-token-invalidation_ELITEA-2601.md
"""

import logging
import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.agents, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000  # publish_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000

CATEGORY = "Quality Assurance"

_SUFFIX = uuid.uuid4().hex[:6]

VALID_SKILL_NAME = f"valid-skill-2601-{_SUFFIX}"
VALID_SKILL_DESCRIPTION = "Validates and formats text content for the ELITEA-2601 fixture"
VALID_SKILL_INSTRUCTIONS = (
    "You are a text-validation skill for automated regression testing. "
    "When invoked, review the provided text for basic formatting issues "
    "and reply with the single word CONFIRMED to prove you were invoked."
)


# NAMING — deliberately NOT "invalid-skill-2601-<suffix>": that string
# contains "valid-skill-2601-<suffix>" as a literal substring, and
# Popper.select_menuitem_by_testid() selects via `.filter(has_text=...)`
# (a SUBSTRING match) + `.first` — attaching "valid-skill-..." would then
# ambiguously match BOTH menu items and silently attach the WRONG one
# (confirmed live this dispatch: it attached "invalid-skill-..." instead).
# "broken-skill" shares no substring with "valid-skill"/"extra-skill".
INVALID_SKILL_NAME = f"broken-skill-2601-{_SUFFIX}"
# Deliberately trips BOTH Critical rules at once: short (well under 100
# chars) AND containing placeholder text (AFS Test Data — a NEW discovery
# beyond ELITEA-2600's AFS, which only ever tripped the length rule alone).
INVALID_SKILL_DESCRIPTION = "[TODO]"
INVALID_SKILL_INSTRUCTIONS = "[TODO] short."

EXTRA_SKILL_NAME = f"extra-skill-2601-{_SUFFIX}"
EXTRA_SKILL_DESCRIPTION = "Second, independently-valid skill for the Part B attach/detach probe"
EXTRA_SKILL_INSTRUCTIONS = (
    "You are a second, independently-valid skill for automated regression "
    "testing of agent publish-token invalidation. When invoked, reply "
    "briefly confirming you were invoked, with no other output."
)

AGENT_NAME = f"validation-test-agent-2601-{_SUFFIX}"
AGENT_DESCRIPTION = "Disposable agent for ELITEA-2601's validation-attribution/token-invalidation test"

# >= 100 chars — the agent's OWN instructions field is independently
# subject to the same "too short" Critical rule as a skill's content
# (confirmed live this dispatch: a shorter draft tripped a THIRD,
# agent-level Critical issue with context=None, muddying the per-skill
# attribution assertions below — this is a distinct, agent-level finding,
# not something to conflate with the skill-attribution mechanism under test).
AGENT_INSTRUCTIONS = (
    "You are a helpful assistant created solely to exercise the agent "
    "publish-validation flow and the publish-token invalidation mechanism "
    "for automated regression testing purposes."
)
AGENT_TAG = "automation"

VERSION_NAME_1 = f"v1-2601-{_SUFFIX}"
VERSION_NAME_2 = f"v2-2601-{_SUFFIX}"
VERSION_NAME_3 = f"v3-2601-{_SUFFIX}"

TOO_SHORT_ISSUE_SNIPPET = "too short"
PLACEHOLDER_ISSUE_SNIPPET = "placeholder"
VALIDATION_FAILED_ERROR = "validation_failed"


def _skill_context(skill_name: str) -> str:
    """Build the exact `critical_issues[]`/`warnings[]`/`recommendations[]`
    entry ``context`` field value used to attribute a validation finding to
    a specific attached skill — literal ``"skill: <name>"`` (confirmed
    live, AFS ELITEA-2601 step 6; matches ``ValidationResult.jsx``'s
    ``buildPlainText()`` rendering: ``${i.field} [${i.context}]: ${i.issue}``).
    """
    return f"skill: {skill_name}"


class TestAgentSkillsValidationAttributionAndTokenInvalidation:
    """ELITEA-2601 — per-skill validation attribution + publish-token invalidation."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2601_agent-with-skills-validation-attribution-and-token-invalidation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_agent_skills_validation_attribution_and_token_invalidation(self, page, agent_api, skill_api):
        """Part A: per-skill Critical-issue attribution on an agent's
        attached skills. Part B: a skill attach AND a skill removal, each
        made to the SAME agent version from a second tab, invalidate a
        held-open publish-wizard's validation token."""
        valid_skill_id = None
        invalid_skill_id = None
        extra_skill_id = None
        agent_id = None
        second_page = None

        try:
            with allure.step(
                "Step 1 — Create a valid skill (>=100-char instructions, no placeholders)"
            ):
                created = skill_api.create_skill(
                    name=VALID_SKILL_NAME,
                    description=VALID_SKILL_DESCRIPTION,
                    instructions=VALID_SKILL_INSTRUCTIONS,
                )
                valid_skill_id = created["id"]
                assert valid_skill_id is not None, "Valid skill should be created with an id"

            with allure.step(
                "Step 2 — Create an invalid skill (short content AND placeholder "
                "text in the SAME instructions field) — creation itself performs "
                "no content-quality validation"
            ):
                created = skill_api.create_skill(
                    name=INVALID_SKILL_NAME,
                    description=INVALID_SKILL_DESCRIPTION,
                    instructions=INVALID_SKILL_INSTRUCTIONS,
                )
                invalid_skill_id = created["id"]
                assert invalid_skill_id is not None, "Invalid skill should still be created successfully"
                assert invalid_skill_id != valid_skill_id, "Invalid skill should have a distinct id"

            with allure.step(
                "Step 2b — Create a THIRD, dedicated valid skill for the Part B "
                "attach/detach probe (own >=100-char, no-placeholder content — "
                "avoids the confound the AFS's own live run hit by reusing the "
                "invalid skill for this probe, which masks the removal direction "
                "behind a genuine validation FAIL instead of a clean token check)"
            ):
                created = skill_api.create_skill(
                    name=EXTRA_SKILL_NAME,
                    description=EXTRA_SKILL_DESCRIPTION,
                    instructions=EXTRA_SKILL_INSTRUCTIONS,
                )
                extra_skill_id = created["id"]
                assert extra_skill_id not in (valid_skill_id, invalid_skill_id), (
                    "Extra skill should have a distinct id from the other two"
                )

            with allure.step(
                "Step 3 — Create an agent, add a Tag (Critical publish gate), "
                "and attach both the valid and invalid skills"
            ):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME, description=AGENT_DESCRIPTION, instructions=AGENT_INSTRUCTIONS,
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
                logger.info("Created agent %r id=%d", AGENT_NAME, agent_id)

                detail_page.add_tag(AGENT_TAG)
                detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

                for skill_name in (VALID_SKILL_NAME, INVALID_SKILL_NAME):
                    detail_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                    assert detail_page.is_skill_attached(skill_name), (
                        f"Skill card for {skill_name!r} should render after attaching"
                    )
                assert "2/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should read '2/5 skills added.' once both are attached"
                )

            with allure.step(
                "Step 4-5-6-7 — Open the Publish wizard, complete Preparation, "
                "Continue; verify validation FAILS with TWO independently-"
                "attributed Critical issues on the invalid skill (too-short AND "
                "placeholder-text as SEPARATE rules), the valid skill carries NO "
                "Critical/Warning entry, and Publish is disabled"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME_1, CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.is_publish_continue_enabled(), (
                    "Continue should be enabled once Name, Category, and agree-checkbox are set"
                )

                validate_response = detail_page.click_publish_continue_and_capture_response(
                    timeout=VALIDATE_TIMEOUT
                )
                validate_body = validate_response.json()
                assert validate_body.get("status") == "FAIL", (
                    f"Expected a FAIL validation status (invalid skill attached), got: {validate_body}"
                )
                assert validate_body.get("counts", {}).get("critical") == 2, (
                    f"Expected exactly 2 Critical issues, got: {validate_body.get('counts')}"
                )

                critical_issues = validate_body.get("critical_issues", [])
                invalid_skill_issues = [
                    i for i in critical_issues if i.get("context") == _skill_context(INVALID_SKILL_NAME)
                ]
                assert len(invalid_skill_issues) == 2, (
                    f"Expected 2 Critical issues attributed to {INVALID_SKILL_NAME!r} "
                    f"(too-short AND placeholder-text as separate rules), got "
                    f"{len(invalid_skill_issues)}: {critical_issues}"
                )
                assert any(
                    TOO_SHORT_ISSUE_SNIPPET in i.get("issue", "").lower() for i in invalid_skill_issues
                ), f"Expected a 'too short' Critical issue for {INVALID_SKILL_NAME!r}, got: {invalid_skill_issues}"
                assert any(
                    PLACEHOLDER_ISSUE_SNIPPET in i.get("issue", "").lower() for i in invalid_skill_issues
                ), (
                    f"Expected a 'placeholder' Critical issue for {INVALID_SKILL_NAME!r}, "
                    f"got: {invalid_skill_issues}"
                )

                # Pass criteria only require NO errors attributed to the valid
                # skill (not that a Suggestion names it — Suggestion content is
                # AI-generated and not deterministic enough to assert on here).
                valid_skill_errors = [
                    i
                    for i in critical_issues + validate_body.get("warnings", [])
                    if i.get("context") == _skill_context(VALID_SKILL_NAME)
                ]
                assert valid_skill_errors == [], (
                    f"Valid skill {VALID_SKILL_NAME!r} should show zero Critical/Warning "
                    f"entries, got: {valid_skill_errors}"
                )

                assert not detail_page.is_publish_confirm_enabled(), (
                    "Publish button should be disabled while Critical issues remain"
                )

            with allure.step(
                "Step 8 — Remove the invalid skill from the agent; verify the "
                "removal persists immediately and the counter drops"
            ):
                detail_page.close_publish_wizard()
                detail_page.remove_skill(INVALID_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.is_skill_attached(INVALID_SKILL_NAME), (
                    "Invalid skill should no longer be attached after removal"
                )
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "Skills counter should read '1/5 skills added.' after removing the invalid skill"
                )

            with allure.step(
                "Step 9 — Re-run validation (fresh Publish wizard); verify it "
                "now PASSES with zero Critical issues and Publish becomes enabled"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.publish_version_name_input.input_value() == "", (
                    "Re-opened Publish wizard should start a fresh, empty Preparation step"
                )
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME_2, CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                )

                revalidate_response = detail_page.click_publish_continue_and_capture_response(
                    timeout=VALIDATE_TIMEOUT
                )
                revalidate_body = revalidate_response.json()
                assert revalidate_body.get("counts", {}).get("critical", -1) == 0, (
                    f"Expected 0 Critical issues with only the valid skill attached, "
                    f"got: {revalidate_body.get('counts')}"
                )
                assert detail_page.is_publish_confirm_enabled(), (
                    "Publish button should be enabled once validation reports 0 Critical issues"
                )

            with allure.step(
                "Step 10-11 — Keep the wizard open on this passing Validation "
                "state (Part B setup) — do NOT close it"
            ):
                assert detail_page.is_publish_confirm_enabled(), (
                    "Wizard state should carry over unchanged into Part B"
                )

            with allure.step(
                "Step 12 — In a second browser tab, open the SAME agent's "
                "Configuration tab directly (?destTab=configuration is REQUIRED "
                "— a bare agent URL in a fresh tab lands on Chat, not Skills, "
                "confirmed live)"
            ):
                second_page = page.context.new_page()
                second_detail_page = AgentDetailPage(second_page)
                second_detail_page.navigate_to_configuration_tab(agent_id)
                second_detail_page.ensure_skills_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in second_detail_page.get_skills_counter_text(), (
                    "Second tab should show the CURRENT skill list (1/5 skills added.)"
                )

            with allure.step(
                "Step 13 — Attach the dedicated extra-skill to the agent from "
                "the second tab; verify the SECOND tab's counter increments "
                "while the FIRST tab's stale wizard summary does NOT live-refresh"
            ):
                second_detail_page.attach_skill(EXTRA_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert second_detail_page.is_skill_attached(EXTRA_SKILL_NAME), (
                    f"Skill card for {EXTRA_SKILL_NAME!r} should render in the second tab"
                )
                assert "2/" in second_detail_page.get_skills_counter_text(), (
                    "Second tab's Skills counter should read '2/5 skills added.'"
                )
                assert "1/" in detail_page.get_skills_counter_text(), (
                    "First tab's background page should NOT live-refresh — still 1/5"
                )

            with allure.step(
                "Step 14-15 — Return to the first tab and attempt Publish; "
                "verify it is rejected with a 400 validation_failed 'modified "
                "since validation' error (ADDITION direction), the SAME message "
                "renders inline, and Publish becomes disabled"
            ):
                publish_response = detail_page.confirm_publish_and_capture_response(timeout=PUBLISH_TIMEOUT)
                assert publish_response.status == 400, (
                    f"Expected 400 from publish with a stale (agent modified) "
                    f"token, got {publish_response.status}"
                )
                publish_body = publish_response.json()
                assert publish_body.get("error") == VALIDATION_FAILED_ERROR, (
                    f"Expected error={VALIDATION_FAILED_ERROR!r}, got: {publish_body}"
                )
                assert "modified" in publish_body.get("msg", "").lower(), (
                    f"Expected a 'modified since validation' msg, got: {publish_body}"
                )
                inline_message = detail_page.get_publish_error_message()
                assert publish_body["msg"] in inline_message, (
                    f"Expected the inline error alert to show the same msg text "
                    f"{publish_body['msg']!r}, got: {inline_message!r}"
                )
                assert not detail_page.is_publish_confirm_enabled(), (
                    "Publish button should become disabled after the validation_failed rejection"
                )
                assert detail_page.publish_confirm_button.is_visible(), (
                    "Wizard should stay showing the Publish control (still "
                    "disabled), not silently lose it"
                )

            with allure.step(
                "Step 16 — Restart validation (Cancel, reopen Publish); verify "
                "a fresh Preparation step and that re-validating now PASSES "
                "(2 genuinely-attached skills, both content-valid)"
            ):
                detail_page.close_publish_wizard()
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.publish_version_name_input.input_value() == "", (
                    "Re-opened Publish wizard should start a fresh, empty Preparation step"
                )
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME_3, CATEGORY, timeout=UI_ELEMENT_TIMEOUT
                )
                retry_validate_response = detail_page.click_publish_continue_and_capture_response(
                    timeout=VALIDATE_TIMEOUT
                )
                retry_validate_body = retry_validate_response.json()
                assert retry_validate_body.get("counts", {}).get("critical", -1) == 0, (
                    f"Expected 0 Critical issues with both attached skills "
                    f"content-valid, got: {retry_validate_body.get('counts')}"
                )
                assert detail_page.is_publish_confirm_enabled(), (
                    "Publish button should be enabled — validation passed again"
                )

            with allure.step(
                "Step 17 — In the second tab, REMOVE the extra-skill; verify "
                "the removal persists immediately (same 'live-persisted' shape "
                "as attach)"
            ):
                second_detail_page.remove_skill(EXTRA_SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert not second_detail_page.is_skill_attached(EXTRA_SKILL_NAME), (
                    "Extra skill should no longer be attached in the second tab after removal"
                )
                assert "1/" in second_detail_page.get_skills_counter_text(), (
                    "Second tab's Skills counter should drop back to '1/5 skills added.'"
                )

            with allure.step(
                "Step 18 — Attempt Publish from the first tab again; verify "
                "the SAME 400 validation_failed rejection fires for the "
                "REMOVAL direction too (AFS Blocked Steps — not independently "
                "confirmed by the analyst; this test's own green run against "
                "the live product IS that confirmation)"
            ):
                removal_publish_response = detail_page.confirm_publish_and_capture_response(
                    timeout=PUBLISH_TIMEOUT
                )
                assert removal_publish_response.status == 400, (
                    f"Expected 400 from publish after a skill REMOVAL on a "
                    f"held-open wizard, got {removal_publish_response.status}"
                )
                removal_publish_body = removal_publish_response.json()
                assert removal_publish_body.get("error") == VALIDATION_FAILED_ERROR, (
                    f"Expected error={VALIDATION_FAILED_ERROR!r} for the "
                    f"removal direction too, got: {removal_publish_body}"
                )
                assert "modified" in removal_publish_body.get("msg", "").lower(), (
                    f"Expected a 'modified since validation' msg for the "
                    f"removal direction, got: {removal_publish_body}"
                )
                assert not detail_page.is_publish_confirm_enabled(), (
                    "Publish button should be disabled again after the second rejection"
                )
        finally:
            with allure.step("Cleanup — close the second tab, delete the agent and the 3 skills"):
                if second_page is not None:
                    try:
                        second_page.close()
                    except Exception as exc:
                        logger.warning("Cleanup: failed to close second tab: %s", exc)
                if agent_id is not None:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Cleanup: deleted agent id=%d", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
                for skill_id in (valid_skill_id, invalid_skill_id, extra_skill_id):
                    if skill_id is not None:
                        try:
                            skill_api.delete_skill(skill_id)
                            logger.info("Cleanup: deleted skill id=%d", skill_id)
                        except Exception as exc:
                            logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
