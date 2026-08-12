"""Skill Publishing — WARN Status Allows Publishing with Warnings (ELITEA-2598).

**Case-text drift (filed as clarification, issue #1463 — see AFS §
Known Defects): live-confirmed the case's "No Icon Skill" scenario is
unautomatable as written** — a skill missing a custom icon returns
``status: "FAIL"`` (CRITICAL, blocks Publish), not ``"WARN"``. This test
automates the LIVE CONTRACT instead: a single fixture skill with a generic
name (WARN-level — matches the case) that DOES have a custom icon and a
tag (both required to avoid FAIL, per ELITEA-2595's finding), demonstrating
the case's actual thesis — a WARN-only issue does not block Publish.

Reuses the same shared Publish wizard page-object methods as ELITEA-2595/
2596 (``SkillDetailPage.open_publish_wizard`` /
``fill_publish_preparation_step`` / ``click_publish_continue`` /
``confirm_publish`` / ``select_version_by_name``) — this case is
effectively ELITEA-2595's happy path with an intentionally generic Name
substituted in, so most of the implementation is shared, not duplicated.

Known defect #614 (see AFS ELITEA-2595 § Known Defects) reproduces here
too: automation re-selects the published version by name after Publish
rather than trusting the app's own unreliable auto-navigation.

Spec: test-specs/skills/l3_skill-publishing-warn-status-allows-publishing_ELITEA-2598.md
"""

from pathlib import Path

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression]

# Reuses the existing repo test-icon asset (already added for ELITEA-2602/2604) —
# resolved relative to this file (pytest's cwd is automation/, not repo root).
ICON_FILE = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000
PUBLISH_TIMEOUT = 15_000

VERSION_NAME = "v1.0"
CATEGORY_NAME = "Quality Assurance"
TAG_NAME = "automation"
SKILL_NAME = "skill"  # deliberately generic — matches the case's own example

# >= 50 chars (live-confirmed threshold).
SKILL_DESCRIPTION = (
    "This skill helps automate common QA regression checks for the ELITEA "
    "test suite by analyzing recent failures and summarizing likely causes."
)
# >= 100 chars (live-confirmed threshold).
SKILL_INSTRUCTIONS = (
    "You are a QA regression assistant for the ELITEA platform test suite. "
    "When asked about a failing test, analyze the described symptom, "
    "summarize the most likely root cause, and suggest the next concrete "
    "diagnostic step. Keep every response concise, factual, and actionable."
)


def _confirm_new_version_via_api(skill_api, skill_id: int, version_name: str, exclude_version_id):
    """API-backed tie-breaker for a ``select_version_by_name`` DOM-poll
    timeout (Known defect #614) — same shape as
    ``test_skill_publish_wizard_happy_path.py``'s helper of the same name.
    """
    skill = skill_api.get_skill(skill_id)
    for version in skill.get("versions", []):
        if (
            version.get("name") == version_name
            and str(version.get("id")) != str(exclude_version_id)
            and version.get("status") == "published"
        ):
            return version.get("id")
    return None


class TestSkillPublishWarnStatusAllowsPublishing:
    """ELITEA-2598 — WARN status allows publishing with warnings (l3/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2598_skill-publishing-warn-status-allows-publishing.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/614", "Known defect #614"
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1463", "Case-text drift clarification"
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_warn_status_does_not_block_publish(self, page, skill_api):
        """A skill with only a WARN-level issue (generic name) validates as
        WARN, not FAIL, and can still be published."""
        # Use the case's own literal generic name UNSUFFIXED (no uuid) —
        # live-confirmed during implementation: appending a uuid suffix
        # (e.g. "skill-a1b2c3d4") reads as a semi-unique compound name to
        # the AI validator and downgrades the generic-name signal from a
        # `warnings` entry to a `recommendations` entry (status PASS, not
        # WARN) — the AFS's own exploration note ("no uniqueness collision
        # observed this run") already anticipated using the bare literal.
        skill_name = SKILL_NAME
        skill_id = None

        detail_page = SkillDetailPage(page)
        soft_failures = []

        try:
            with allure.step(
                "Step 1 — Create a skill with a generic/non-descriptive "
                "name but valid description and instructions"
            ):
                skill = skill_api.create_skill(
                    name=skill_name,
                    description=SKILL_DESCRIPTION,
                    instructions=SKILL_INSTRUCTIONS,
                )
                skill_id = skill["id"]
                assert skill_id, "Expected a numeric id for the created skill"

                detail_page.navigate(skill_id)
                detail_page.verify_on_detail_page()
                base_version_id = detail_page.get_version_id()

            with allure.step(
                "Step 2 — Ensure the skill has a custom icon set and at "
                "least one tag (required — see AFS Test Data drift note, "
                "issue #1463: missing icon/tags are FAIL-blocking, not "
                "WARN-level)"
            ):
                # Tag first, saved via the form's own Save button; icon
                # SECOND via the dedicated edit-mode upload flow (persists
                # itself immediately through its own PUT) — same ordering
                # rationale as test_skill_publish_wizard_happy_path.py.
                detail_page.add_tag(TAG_NAME)
                assert detail_page.get_tags() == [TAG_NAME], (
                    f"Expected exactly [{TAG_NAME!r}] after adding the tag, "
                    f"got: {detail_page.get_tags()!r}"
                )
                save_response = detail_page.save_edits(timeout=15000)
                assert save_response.status == 200, (
                    f"Expected 200 from the edit-flow Save (persists the "
                    f"tag), got {save_response.status}"
                )

                icon_src = detail_page.upload_skill_icon_edit_mode(
                    ICON_FILE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert icon_src, "Expected a non-empty custom icon src after upload"

            with allure.step(
                "Step 3 — Open the publish wizard and proceed to Validation "
                "(fill version name + category, accept Publishing Terms, "
                'click "Continue")'
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                validate_response = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                validate_body = validate_response.json()

            with allure.step("Step 4 — Verify validation returns WARN status (not FAIL)"):
                assert validate_body.get("status") == "WARN", (
                    f"Expected status=WARN with a valid icon+tag present "
                    f"(only the generic-name issue should remain), got: "
                    f"{validate_body!r}"
                )
                assert validate_response.status == 200, (
                    f"publish_skill_validate should return 200 for a WARN "
                    f"result, got {validate_response.status}"
                )

            with allure.step(
                "Step 5 — Verify the warning message mentions the generic/"
                "non-descriptive name"
            ):
                warnings = validate_body.get("warnings", [])
                generic_name_hit = any(
                    entry.get("field") == "name"
                    and "generic" in (entry.get("issue") or "").lower()
                    for entry in warnings
                )
                assert generic_name_hit, (
                    "Expected a warnings entry field='name' mentioning "
                    f"'generic', got: {warnings!r}"
                )

            with allure.step(
                "Step 6 — Verify critical_issues is EMPTY (the icon/tags "
                "CRITICAL gates are correctly cleared — the corrected, "
                "live-true equivalent of the case's unautomatable 'missing "
                "icon warning' assertion, per issue #1463)"
            ):
                critical_issues = validate_body.get("critical_issues", [])
                assert critical_issues == [], (
                    f"Expected an empty critical_issues list with a valid "
                    f"icon+tag present, got: {critical_issues!r}"
                )

            with allure.step('Step 7 — Verify the "Next"/"Publish" button is still ENABLED'):
                assert detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should stay enabled "
                    "for a WARN (non-FAIL) status"
                )

            with allure.step('Step 8/9 — Click "Publish"; publishing completes successfully'):
                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, (
                    f"publish_skill POST should return 200, got {publish_status}"
                )

            with allure.step(
                "Step 10 — Re-select the newly published version by name "
                "(auto-navigation is unreliable — Known defect #614), then "
                "verify the skill appears in the Catalog"
            ):
                try:
                    detail_page.select_version_by_name(
                        VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                    )
                    version_dom_converged = True
                except AssertionError as select_exc:
                    version_dom_converged = False
                    new_version_id = _confirm_new_version_via_api(
                        skill_api, skill_id, VERSION_NAME,
                        exclude_version_id=base_version_id,
                    )
                    if new_version_id is None:
                        raise AssertionError(
                            f"{select_exc} (API tie-breaker ALSO disagrees — "
                            f"no distinct 'published' version named "
                            f"{VERSION_NAME!r} exists server-side either; "
                            "this is NOT confirmed as known defect #614's "
                            "cosmetic staleness)"
                        ) from select_exc
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/614: "
                        "select_version_by_name's DOM poll never converged on "
                        f"{VERSION_NAME!r} even though the API confirms a "
                        f"distinct published version (id={new_version_id}) "
                        f"already exists (client-side status staleness, not "
                        f"a data bug): {select_exc}"
                    )

                if version_dom_converged:
                    assert detail_page.get_version_selector_value() == VERSION_NAME, (
                        f"VERSION selector should show {VERSION_NAME!r} once "
                        "explicitly selected"
                    )

                catalog_page = AgentHubPage(page)
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=NAVIGATION_TIMEOUT)
                catalog_page.wait_for_any_skill_card(timeout=NAVIGATION_TIMEOUT)
                catalog_page.wait_for_category_heading(CATEGORY_NAME, timeout=NAVIGATION_TIMEOUT)

                visible_headings = catalog_page.get_visible_category_heading_texts()
                assert CATEGORY_NAME in visible_headings, (
                    f"Expected the {CATEGORY_NAME!r} category section to be "
                    f"visible in the Catalog's Skills tab, found: {visible_headings!r}"
                )

                skill_card = catalog_page.get_skill_card(skill_name, category=CATEGORY_NAME)
                skill_card.first.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)
                assert skill_card.count() >= 1, (
                    f"Expected a Catalog card for {skill_name!r} under the "
                    f"{CATEGORY_NAME!r} category section after publishing, found none"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — the full publish flow above "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            with allure.step("Cleanup — delete the published skill (all versions)"):
                if skill_id:
                    try:
                        skill_api.delete_skill(skill_id)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup skill {skill_id}: {cleanup_exc}")
