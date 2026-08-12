"""Skill Publishing — Token Invalidation and TTL Expiration (ELITEA-2597).

Verifies the Publish wizard's ``validation_token`` (issued by
``publish_skill_validate``) is rejected by ``publish_skill`` when:

  Part A — the skill's active version was MODIFIED after the token was
    issued (a second browser tab saves new instructions while the first
    tab's wizard still holds the now-stale token).
  Part B — MORE THAN 300s (the confirmed-live 5-minute TTL) elapsed since
    the token was issued, with the skill left unmodified.

Both causes return ``400 {"error": "validation_token_invalid", "msg": ...}``
— the SAME ``error`` code, a DIFFERENT ``msg`` text distinguishing
"modified" from "expired" (AFS Axis 2 addition — asserting only the HTTP
status can't tell the two causes apart; the ``msg`` string is the real
assertion surface).

Test case: ELITEA-2597
AFS: test-specs/skills/l2_skill-publishing-token-invalidation-and-ttl-expiration_ELITEA-2597.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

CATEGORY = "Quality Assurance"
# Same fixture image + repo-root-relative resolution as
# test_skill_fork_end_to_end.py / test_skill_custom_icon_visibility_across_ui.py
# (parents[4]: skills -> ui -> tests -> automation -> repo root).
ICON_PATH = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)
# >= 50 chars — live-confirmed threshold (same gap as ELITEA-2595, issue #1463).
DESCRIPTION = (
    "Analyzes failing regression-test symptoms and suggests concrete "
    "diagnostic next steps for the ELITEA platform test suite (ELITEA-2597 fixture)."
)
# >= 100 chars — live-confirmed threshold. Bounded, task-specific phrasing —
# a blanket "reply X to any prompt" directive (originally used here) trips
# the AI content-quality gate's prompt-injection heuristic and returns
# 422/FAIL (confirmed live this run: critical_issues[0].field="instructions",
# "Contains a blanket instruction ... functions as an unsafe prompt-injection
# style directive"), which would leave validation_token null and make this
# fixture unusable for the case Part A/B are actually testing.
INSTRUCTIONS = (
    "You are a QA regression assistant for the ELITEA platform test suite. "
    "When asked about a failing automated test, analyze the described "
    "symptom, summarize the most likely root cause, and suggest the next "
    "concrete diagnostic step. Keep every response concise and factual."
)
MODIFIED_INSTRUCTIONS = INSTRUCTIONS + " Modified via the second tab for Part A."

TOKEN_INVALID_ERROR = "validation_token_invalid"
# TTL confirmed live = 300s exactly; wait a margin over it (AFS's own
# exploration used 320-330s successfully).
TTL_WAIT_SECONDS = 320


def _make_skill_ready_for_publish(page, skill_api, name_prefix: str):
    """Create a skill via API, then add a tag + custom icon via UI (edit
    mode) and Save — the WARN/PASS prerequisite (issue #1463: a skill with
    only long description/instructions still returns FAIL,
    ``validation_token: null``, at ``publish_skill_validate``).

    Returns ``(detail_page, skill_id)`` — the page is already positioned
    on the skill's detail page.
    """
    ts = int(time.time() * 1000)
    skill_name = f"{name_prefix}-{ts}"[:32]

    created = skill_api.create_skill(
        name=skill_name, description=DESCRIPTION, instructions=INSTRUCTIONS,
    )
    skill_id = created["id"]
    logger.info("Created skill id=%s name=%s", skill_id, skill_name)

    detail_page = SkillDetailPage(page)
    detail_page.navigate(skill_id)
    # Icon FIRST: upload_skill_icon_edit_mode() persists immediately via its
    # own POST+PUT pair (independent of the Save button/Formik dirty state)
    # and re-fetches the skill — doing it AFTER add_tag() risks that refetch
    # re-initializing the form from server state and discarding the
    # not-yet-saved tag (confirmed live this run: reversed order left
    # skill-save-button disabled, save_edits() timed out with no PUT fired).
    detail_page.upload_skill_icon_edit_mode(ICON_PATH)
    # Tags MUST use underscores — hyphens are silently rejected (same root
    # cause documented in test_skill_fork_non_base_version.py / issue #1445).
    detail_page.add_tag("elitea_2597")
    assert detail_page.get_tags() == ["elitea_2597"], (
        f"Expected the tag to commit before Save, got: {detail_page.get_tags()!r}"
    )
    detail_page.save_edits()
    logger.info("Skill id=%s ready for publish (icon+tag added)", skill_id)
    return detail_page, skill_id


class TestSkillPublishTokenInvalidationAndTTL:
    """ELITEA-2597 — Publish wizard token invalidation (Part A) and TTL expiration (Part B)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2597_skill-publishing-token-invalidation-and-ttl-expiration.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_publish_token_invalidated_by_modification(self, page, skill_api):
        """Part A — a stale ``validation_token`` (skill modified after
        issuance) is rejected by ``publish_skill`` with a "modified" error,
        Publish becomes disabled, and re-validation is the only way forward."""
        skill_id = None
        try:
            with allure.step(
                "Step 1 — Create a skill with valid content (description "
                ">=50 chars, instructions >=100 chars, 1 tag, custom icon)"
            ):
                detail_page, skill_id = _make_skill_ready_for_publish(
                    page, skill_api, "el-2597-modify"
                )

            with allure.step(
                "Step 2 — Open the Publish wizard, complete Preparation, "
                "Continue; verify 200 + status != FAIL + non-null validation_token"
            ):
                detail_page.open_publish_wizard()
                detail_page.fill_publish_preparation_step("v1.0-token-probe", CATEGORY)
                validate_response = detail_page.click_publish_continue()
                assert validate_response.status == 200, (
                    f"Expected 200 from publish_skill_validate, got "
                    f"{validate_response.status}: {validate_response.text()}"
                )
                validate_body = validate_response.json()
                assert validate_body.get("status") != "FAIL", (
                    f"Expected a non-FAIL validation status, got: {validate_body}"
                )
                assert validate_body.get("validation_token"), (
                    f"Expected a non-null validation_token, got: {validate_body}"
                )
                assert detail_page.is_publish_confirm_enabled(), (
                    "Publish button should be enabled after a non-FAIL validation"
                )

            with allure.step(
                "Step 3 — WITHOUT closing the wizard, open the same skill "
                "in a second tab and modify the instructions; Save"
            ):
                second_page = page.context.new_page()
                second_detail_page = SkillDetailPage(second_page)
                second_detail_page.navigate(skill_id)
                second_detail_page.fill_instructions(MODIFIED_INSTRUCTIONS)
                second_save_response = second_detail_page.save_edits()
                assert second_save_response.status == 200, (
                    f"Expected 200 from the second tab's edit-flow save, got "
                    f"{second_save_response.status}"
                )
                second_page.close()

            with allure.step(
                "Step 4 — Return to the first tab/wizard and click Publish; "
                "verify 400 validation_token_invalid with the 'modified' msg, "
                "the same text renders inline, and Publish becomes disabled"
            ):
                publish_response = detail_page.confirm_publish()
                assert publish_response.status == 400, (
                    f"Expected 400 from publish_skill with a stale "
                    f"(modified) token, got {publish_response.status}"
                )
                body = publish_response.json()
                assert body.get("error") == TOKEN_INVALID_ERROR, (
                    f"Expected error={TOKEN_INVALID_ERROR!r}, got: {body}"
                )
                assert "modified" in body.get("msg", "").lower(), (
                    f"Expected a 'modified since validation' msg, got: {body}"
                )
                inline_message = detail_page.get_publish_error_message()
                assert body["msg"] in inline_message, (
                    f"Expected the inline dialog error to show the same msg "
                    f"text {body['msg']!r}, got: {inline_message!r}"
                )
                assert not detail_page.is_publish_confirm_enabled(), (
                    "Publish button should become disabled after the "
                    "validation_token_invalid rejection"
                )
                # Wizard stays on the Validation step (Publish button still
                # rendered, just disabled) — does NOT silently reset to
                # Preparation or auto-refire validation (AFS Axis 2).
                assert detail_page.publish_confirm_button.is_visible(), (
                    "Wizard should stay on the Validation step after the "
                    "rejection, not reset to Preparation"
                )

            with allure.step(
                "Step 5 — The only available action is Cancel; re-opening "
                "Publish from the overflow menu runs a fresh Preparation cycle"
            ):
                detail_page.close_publish_wizard()
                detail_page.open_publish_wizard()
                assert detail_page.publish_version_name_input.input_value() == "", (
                    "Re-opened Publish wizard should start a fresh "
                    "Preparation step (empty version name), not resume the "
                    "stale Validation step"
                )
                detail_page.close_publish_wizard()
        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(skill_id)
                    logger.info("Deleted skill id=%s", skill_id)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2597_skill-publishing-token-invalidation-and-ttl-expiration.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.slow
    def test_publish_token_expires_after_ttl(self, page, skill_api):
        """Part B — a ``validation_token`` older than 300s (the 5-minute
        TTL) is rejected by ``publish_skill`` with an "expired" error,
        distinct from Part A's "modified" error though sharing the same
        ``error`` code.

        Deliberate, DECLARED exception to the "no sleep/waitForTimeout"
        convention (``.agents/conventions.md`` § Hard don'ts) per the
        declared-improvisation protocol (``.agents/role-overrides.md`` §
        Every role): this test's OWN subject is "does the server enforce a
        300-second TTL" — waiting real wall-clock time IS the correct tool
        here, not a workaround for a UI-synchronization problem. There is
        no page-state condition to wait ON (nothing changes client-side
        during the wait) — the condition is the wall clock crossing 300s
        past the token's issuance moment. See AFS ELITEA-2597 § Automation
        Hints. Run as its OWN test function (not combined with Part A) so a
        CI timeout budget or ``-m "not slow"`` filter can exclude it
        independently.
        """
        skill_id = None
        try:
            with allure.step(
                "Step 6 — Create a skill with valid content, open the "
                "Publish wizard, complete Preparation, Continue; capture "
                "the validation_token issuance moment"
            ):
                detail_page, skill_id = _make_skill_ready_for_publish(
                    page, skill_api, "el-2597-ttl"
                )
                detail_page.open_publish_wizard()
                detail_page.fill_publish_preparation_step("v1.0-ttl-probe", CATEGORY)
                validate_response = detail_page.click_publish_continue()
                assert validate_response.status == 200, (
                    f"Expected 200 from publish_skill_validate, got "
                    f"{validate_response.status}: {validate_response.text()}"
                )
                validate_body = validate_response.json()
                assert validate_body.get("validation_token"), (
                    f"Expected a non-null validation_token, got: {validate_body}"
                )
                issued_at = time.time()
                logger.info(
                    "validation_token issued for skill id=%s at %s — waiting "
                    "%ds for TTL expiration", skill_id, issued_at, TTL_WAIT_SECONDS,
                )

            with allure.step(
                f"Step 7 — Wait {TTL_WAIT_SECONDS}s (>300s TTL) without "
                "touching the skill or the wizard — real elapsed wall-clock "
                "time, no client-side condition to wait on (see docstring)"
            ):
                time.sleep(TTL_WAIT_SECONDS)

            with allure.step(
                "Step 8 — Click Publish (token now expired, skill "
                "unmodified); verify 400 validation_token_invalid with the "
                "'expired' msg (distinct from Part A's 'modified' msg), "
                "the same text renders inline, Publish becomes disabled"
            ):
                publish_response = detail_page.confirm_publish()
                assert publish_response.status == 400, (
                    f"Expected 400 from publish_skill with an expired "
                    f"token, got {publish_response.status}"
                )
                body = publish_response.json()
                assert body.get("error") == TOKEN_INVALID_ERROR, (
                    f"Expected error={TOKEN_INVALID_ERROR!r}, got: {body}"
                )
                assert "expired" in body.get("msg", "").lower(), (
                    f"Expected an 'expired' msg (distinct from the "
                    f"modification-cause msg), got: {body}"
                )
                inline_message = detail_page.get_publish_error_message()
                assert body["msg"] in inline_message, (
                    f"Expected the inline dialog error to show the same msg "
                    f"text {body['msg']!r}, got: {inline_message!r}"
                )
                assert not detail_page.is_publish_confirm_enabled(), (
                    "Publish button should become disabled after the "
                    "validation_token_invalid rejection"
                )

            with allure.step(
                "Step 9 — The only available action is Cancel; re-opening "
                "Publish from the overflow menu runs a fresh Preparation cycle"
            ):
                detail_page.close_publish_wizard()
                detail_page.open_publish_wizard()
                assert detail_page.publish_version_name_input.input_value() == "", (
                    "Re-opened Publish wizard should start a fresh "
                    "Preparation step (empty version name), not resume the "
                    "stale Validation step"
                )
                detail_page.close_publish_wizard()
        finally:
            with allure.step("Cleanup — delete the skill created for this test"):
                if skill_id is not None:
                    skill_api.delete_skill(skill_id)
                    logger.info("Deleted skill id=%s", skill_id)
