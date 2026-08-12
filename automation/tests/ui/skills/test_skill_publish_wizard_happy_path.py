"""Skill Publishing Wizard — Happy Path (ELITEA-2595).

Creates a disposable skill (seeded via ``SkillAPI.create_skill()`` for
speed/determinism — AFS § Automation Hints), adds a tag and a custom icon
(both REQUIRED prerequisites for the AI ``publish_skill_validate`` gate to
avoid an outright FAIL — case-text drift, not documented in the case's own
Test Data table, filed as CLARIFICATION
https://github.com/EliteaAI/elitea-testing-public/issues/1463, see AFS §
Known Defects), then publishes it through the 3-step Publish wizard
(Preparation -> Validation -> Publishing) and verifies it appears in the
Catalog's Skills tab under its selected Category.

Publish is gated by the AI ``publish_skill_validate`` content-quality check
(never FAIL given the seeded description/instructions length + icon + tag),
mirroring ``test_agent_publish_unpublish_version.py``'s (ELITEA-1892)
handling of the identical shared wizard for the Agent surface.

Two MINOR, isolated, already-filed product defects reproduce here, same
handling as the Agent flow:

1. https://github.com/EliteaAI/elitea-testing-public/issues/614 — the app's
   own post-Publish auto-navigation to the new version is unreliable (a
   network trace shows the app briefly navigating to the new version then
   silently reverting to the previously-active one). This test explicitly
   re-selects the new version by name
   (``SkillDetailPage.select_version_by_name()``) instead of trusting
   auto-navigation, falling back to an API tie-breaker
   (``_confirm_new_version_via_api``) if the DOM poll never converges —
   same principle as ``test_agent_publish_unpublish_version.py``.
2. https://github.com/EliteaAI/elitea-testing-public/issues/611 — the
   Publish wizard Stepper's custom step-icon leaks MUI-internal props onto
   the DOM ``<svg>``, producing React console warnings on every render. The
   console-cleanliness check filters this (and the already-filed, unrelated
   https://github.com/EliteaAI/elitea-testing-public/issues/554 toolkits-404
   race) via the same soft-assertion mechanism
   ``test_agent_publish_unpublish_version.py`` established.

Spec: test-specs/skills/l2_skill-publishing-wizard-happy-path_ELITEA-2595.md
"""

import uuid
from pathlib import Path

import allure
import pytest
from pages.agent_hub_page import AgentHubPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p1, pytest.mark.regression]

# Reuses the existing repo test-icon asset (already added for ELITEA-2602/2604) —
# resolved relative to this file (pytest's cwd is automation/, not repo root).
ICON_FILE = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000  # publish_skill_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000

VERSION_NAME = "v1.0"
CATEGORY_NAME = "Quality Assurance"
TAG_NAME = "automation"

# >= 50 chars (live-confirmed threshold), contains an action verb ("helps")
# to also clear the "lacks action verbs" WARNING for a clean PASS.
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


# Known defect #611 — confirmed live for the Agent Publish flow (ELITEA-1892)
# and reproduces identically here (same shared PublishWizardModal.jsx
# Stepper): the custom step-icon (SvgCheckedIcon) forwards MUI-internal
# props onto the underlying DOM <svg>, producing two distinct React
# dev-warning shapes depending on the prop's type. Matching is anchored on
# the component name (stable across both shapes), combined with an OR of
# both phrase substrings.
def _is_known_defect_611(text: str) -> bool:
    if "SvgCheckedIcon" not in text:
        return False
    return "non-boolean attribute" in text or "does not recognize the" in text


# Known defect #554 (already filed, unrelated) — an RTK-Query timing race in
# EliteaUI/src/api/toolkits.js's toolkitTypes endpoint firing before
# useSelectedProjectId() resolves, 404ing with an empty projectId segment.
# Confirmed reproducible on any full page load (not just Credentials, where
# it was first filed) — this test's own initial navigate() is one. Matched
# on msg.location.url (not msg.text alone, which carries no URL), never a
# blanket "any 404" filter.
def _is_known_554_toolkits_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _confirm_new_version_via_api(skill_api, skill_id: int, version_name: str, exclude_version_id):
    """API-backed tie-breaker for a ``select_version_by_name`` DOM-poll
    timeout (Known defect #614) — the Skill-surface analog of
    ``test_agent_publish_unpublish_version.py``'s
    ``_confirm_new_version_via_api()``.

    Returns the new version's numeric id if the API confirms a distinct,
    published version named *version_name* exists server-side; ``None``
    if no such version is found (i.e. NOT confirmed as the known defect's
    cosmetic staleness — a genuinely different, real bug).
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


class TestSkillPublishWizardHappyPath:
    """ELITEA-2595 — Skill Publishing Wizard, happy path (l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2595_skill-publishing-wizard-happy-path.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/611", "Known defect #611"
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/614", "Known defect #614"
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1463", "Case-text drift clarification"
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_publish_skill_happy_path(self, page, skill_api):
        """A skill with valid content, a tag, and a custom icon can be
        published through the 3-step wizard and appears in the Catalog."""
        skill_name = f"test-publish-skill-{uuid.uuid4().hex[:8]}"[:32]
        skill_id = None

        detail_page = SkillDetailPage(page)
        # Console messages are captured starting BEFORE Step 1's own
        # navigate() (a full page load) so the listener actually observes
        # both the Stepper's later renders (#611) and Step 1's own
        # navigation noise (#554) — same discipline as
        # test_agent_publish_unpublish_version.py.
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        soft_failures = []

        try:
            with allure.step(
                "Step 1/2 — Create the skill (seeded via API, per AFS "
                "Automation Hints) and navigate to its detail page; "
                "confirm it was created successfully"
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
                assert detail_page.get_name() == skill_name, (
                    f"Expected skill name {skill_name!r} on the detail page, "
                    f"got {detail_page.get_name()!r}"
                )
                base_version_id = detail_page.get_version_id()

            with allure.step(
                "Step 3 — Add a tag and a custom icon to the skill (both "
                "required to avoid an outright FAIL at Validation — case-"
                "text drift, CLARIFICATION #1463)"
            ):
                # Tag first, saved via the form's own Save button; icon
                # SECOND via the dedicated edit-mode upload flow (persists
                # itself immediately through its own PUT). This ordering
                # avoids the icon upload's server-side invalidation
                # (Formik's enableReinitialize refetch) racing/clobbering
                # the not-yet-saved local tag-chip form state.
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
                'Step 4 — Open the skill\'s overflow ("Skill" ⋮) menu -> '
                'VERSION group -> "Publish"; wizard opens on Step 1 Preparation'
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.publish_version_name_input.is_visible(), (
                    "Publish wizard Preparation step should show a "
                    "Version-name input"
                )
                assert not detail_page.is_publish_continue_enabled(), (
                    "Continue should stay disabled before Name/Category/"
                    "Terms-agreement are all filled"
                )

            with allure.step(
                "Step 5/6 — Enter a valid Version name and select a "
                'Category; check "I agree with the Publishing Terms"'
            ):
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.is_publish_continue_enabled(), (
                    "Continue should become enabled once Name, Category, "
                    "and the agree-checkbox are all set"
                )

            with allure.step(
                'Step 7 — Click "Continue"; the Validation step renders '
                "the publish_skill_validate result"
            ):
                validate_response = detail_page.click_publish_continue(
                    timeout=VALIDATE_TIMEOUT
                )
                validate_body = validate_response.json()

            with allure.step(
                "Step 8 — Verify validation does NOT return FAIL — status "
                'is WARN or PASS given the icon+tag+length prerequisites; '
                '"Publish" is enabled'
            ):
                assert validate_body.get("status") != "FAIL", (
                    f"publish_skill_validate should not return FAIL given the "
                    f"seeded description/instructions length + icon + tag, "
                    f"got status={validate_body.get('status')!r}, "
                    f"critical_issues={validate_body.get('critical_issues')!r}"
                )
                assert validate_response.status == 200, (
                    f"publish_skill_validate should return 200 for a "
                    f"WARN/PASS result, got {validate_response.status}"
                )
                assert detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be enabled — "
                    "publish_skill_validate did not report FAIL"
                )

            with allure.step(
                'Step 9 — Click "Publish"; publishing completes successfully'
            ):
                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, (
                    f"publish_skill POST should return 200, got {publish_status}"
                )

            with allure.step(
                "Console-cleanliness check around the Publish wizard "
                "(known, isolated, non-blocking React warnings — #611 — "
                "soft-asserted; the already-filed, unrelated #554 toolkits "
                "404 from Step 1's own page load is filtered out)"
            ):
                unexpected_errors = [
                    m.text for m in console_errors
                    if not _is_known_defect_611(m.text)
                    and not _is_known_554_toolkits_404(m)
                ]
                assert not unexpected_errors, (
                    "Expected no UNEXPECTED console errors around the "
                    f"Publish wizard, got: {unexpected_errors!r}"
                )
                known_defect_errors = [
                    m.text for m in console_errors if _is_known_defect_611(m.text)
                ]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/611: "
                        f"React 'non-boolean attribute' (SvgCheckedIcon) console "
                        f"error(s) on the Publish wizard: {len(known_defect_errors)} occurrence(s)"
                    )

            with allure.step(
                "Step 10 — Re-select the newly published version by name "
                "from the VERSION dropdown (auto-navigation is unreliable "
                "— Known defect #614, reproduces for skills too)"
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
                    # Re-open the dropdown (select_version_by_name's own
                    # select+reload cycle leaves it closed) to confirm the
                    # new version is listed alongside 'base'.
                    detail_page.open_version_selector()
                    assert detail_page.is_version_option_visible(
                        VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                    ), f"VERSION dropdown should list the new {VERSION_NAME!r} version"
                    assert detail_page.is_version_option_visible(
                        "base", timeout=UI_ELEMENT_TIMEOUT
                    ), "VERSION dropdown should still list the original 'base' version"
                    detail_page.close_versions_menu()

            with allure.step(
                "Step 11 — Navigate to the Catalog's Skills tab; the "
                "published skill appears under its selected Category"
            ):
                catalog_page = AgentHubPage(page)
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=NAVIGATION_TIMEOUT)
                catalog_page.wait_for_any_skill_card(timeout=NAVIGATION_TIMEOUT)

                visible_headings = catalog_page.get_visible_category_heading_texts()
                assert CATEGORY_NAME in visible_headings, (
                    f"Expected the {CATEGORY_NAME!r} category section to be "
                    f"visible in the Catalog's Skills tab, found: {visible_headings!r}"
                )

            with allure.step(
                "Step 12 — Verify the published skill's card details: "
                "name matches the skill's live Name field"
            ):
                skill_card = catalog_page.get_skill_card(skill_name)
                skill_card.first.wait_for(state="visible", timeout=NAVIGATION_TIMEOUT)
                assert skill_card.count() >= 1, (
                    f"Expected a Catalog card for {skill_name!r} after publishing, "
                    f"found none"
                )

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — the full publish flow above "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            with allure.step("Cleanup — delete the disposable skill (all versions)"):
                if skill_id:
                    try:
                        skill_api.delete_skill(skill_id)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup skill {skill_id}: {cleanup_exc}")
