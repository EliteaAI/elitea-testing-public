"""Skill Publishing — AI Validation Blockers (ELITEA-2596).

Verifies that ``publish_skill_validate`` correctly blocks publishing (status
``FAIL``, Publish button disabled) for three distinct content-quality
problems: short content (below the length gate), placeholder/draft text, and
hardcoded secrets/API keys in the Instructions field. Each fixture skill is
seeded via ``SkillAPI.create_skill()`` (per AFS § Automation Hints — no
UI-typing needed, the case's own steps don't mandate UI creation) and driven
through the Publish wizard's Preparation -> Validation steps only — Publish
never becomes enabled in any of the three scenarios, so this case never
reaches the Publishing step.

Every response also carries icon/tags CRITICAL issues (the fixture skills
have neither) — assertions target the SPECIFIC named issue's presence in
``critical_issues`` via list membership, never response equality/exact
count (AFS Axis 2), so this test stays correct regardless of the icon/tags
rule's independent evolution.

Spec: test-specs/skills/l2_skill-publishing-ai-validation-blockers_ELITEA-2596.md
"""

import uuid

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
VALIDATE_TIMEOUT = 30_000  # publish_skill_validate is AI-backed — variable latency

VERSION_NAME = "v1.0"
CATEGORY_NAME = "Quality Assurance"


def _has_critical_issue(critical_issues: list, field: str, contains: str, source: str | None = None) -> bool:
    """Return True if *critical_issues* contains an entry whose ``field``
    equals *field*, whose ``issue`` text contains *contains*
    (case-insensitive substring — AI-generated wording is stable in
    content but not guaranteed byte-identical across runs), and (if
    given) whose ``source`` equals *source*.
    """
    for entry in critical_issues:
        if entry.get("field") != field:
            continue
        if source is not None and entry.get("source") != source:
            continue
        if contains.lower() in (entry.get("issue") or "").lower():
            return True
    return False


class TestSkillPublishAiValidationBlockers:
    """ELITEA-2596 — Skill Publishing, AI validation blockers (l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2596_skill-publishing-ai-validation-blockers.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_short_content_placeholder_and_secrets_block_publish(self, page, skill_api):
        """Short content, placeholder text, and hardcoded secrets each
        independently produce a FAIL validation status with Publish
        disabled."""
        run_id = uuid.uuid4().hex[:8]
        detail_page = SkillDetailPage(page)
        skill_ids: list[int] = []

        try:
            # ----------------------------------------------------------------
            # Scenario 1 — Short content
            # ----------------------------------------------------------------
            with allure.step(
                "Step 1 — Create a skill with short content (Description "
                '"Short", Instructions "Do it" — both well under the live '
                "length thresholds)"
            ):
                short_skill = skill_api.create_skill(
                    name=f"short-skill-{run_id}"[:32],
                    description="Short",
                    instructions="Do it",
                )
                short_skill_id = short_skill["id"]
                skill_ids.append(short_skill_id)
                assert short_skill_id, "Expected a numeric id for the short-content skill"

            with allure.step(
                "Step 2 — Open the skill's overflow menu -> Publish -> fill "
                "Preparation step -> click Continue"
            ):
                detail_page.navigate(short_skill_id)
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                short_response = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                short_body = short_response.json()

            with allure.step(
                "Step 3 — Verify the validation error indicates content is "
                "too short (description AND instructions both under-length)"
            ):
                assert short_body.get("status") == "FAIL", (
                    f"Expected status=FAIL for short content, got: {short_body!r}"
                )
                critical_issues = short_body.get("critical_issues", [])
                assert _has_critical_issue(critical_issues, "description", "too short"), (
                    f"Expected a critical_issues entry field='description' "
                    f"mentioning 'too short', got: {critical_issues!r}"
                )
                assert _has_critical_issue(critical_issues, "instructions", "too short"), (
                    f"Expected a critical_issues entry field='instructions' "
                    f"mentioning 'too short', got: {critical_issues!r}"
                )

            with allure.step('Step 4 — Verify the "Publish" button is disabled'):
                assert not detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be disabled "
                    "when status is FAIL"
                )

            # ----------------------------------------------------------------
            # Scenario 2 — Placeholder text
            # ----------------------------------------------------------------
            with allure.step(
                "Step 5 — Create a second skill with placeholder text "
                "([replace this], TODO) in description/instructions"
            ):
                placeholder_skill = skill_api.create_skill(
                    name=f"placeholder-skill-{run_id}"[:32],
                    description="[replace this with actual description]",
                    instructions="TODO: add instructions",
                )
                placeholder_skill_id = placeholder_skill["id"]
                skill_ids.append(placeholder_skill_id)
                assert placeholder_skill_id, "Expected a numeric id for the placeholder skill"

            with allure.step(
                "Step 6 — Repeat the wizard flow (Publish -> Preparation -> "
                "Continue) for the placeholder skill"
            ):
                detail_page.navigate(placeholder_skill_id)
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                placeholder_response = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                placeholder_body = placeholder_response.json()

            with allure.step(
                "Step 7 — Verify the validation error indicates placeholder "
                "text was detected (AI-generated, source='ai')"
            ):
                assert placeholder_body.get("status") == "FAIL", (
                    f"Expected status=FAIL for placeholder content, got: {placeholder_body!r}"
                )
                placeholder_issues = placeholder_body.get("critical_issues", [])
                placeholder_hit = any(
                    entry.get("source") == "ai"
                    and entry.get("field") in ("description", "instructions")
                    and any(
                        phrase in (entry.get("issue") or "").lower()
                        for phrase in ("placeholder", "todo", "draft")
                    )
                    for entry in placeholder_issues
                )
                assert placeholder_hit, (
                    "Expected a critical_issues entry with source='ai' "
                    "referencing a placeholder/draft marker, got: "
                    f"{placeholder_issues!r}"
                )

            with allure.step('Step 8 — Verify the "Publish" button is disabled'):
                assert not detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be disabled "
                    "when status is FAIL"
                )

            # ----------------------------------------------------------------
            # Scenario 3 — Hardcoded secrets/API keys
            # ----------------------------------------------------------------
            with allure.step(
                "Step 9 — Create a third skill with hardcoded secrets/API "
                "keys in instructions"
            ):
                secrets_skill = skill_api.create_skill(
                    name=f"secrets-skill-{run_id}"[:32],
                    description=(
                        "Valid description text here, padded well beyond "
                        "the fifty-character minimum threshold."
                    ),
                    instructions=(
                        "Use API key: sk-1234567890abcdef and password: "
                        "MySecretPass123 to authenticate, then proceed with "
                        "the requested task exactly as described by the user "
                        "in their original message to this assistant."
                    ),
                )
                secrets_skill_id = secrets_skill["id"]
                skill_ids.append(secrets_skill_id)
                assert secrets_skill_id, "Expected a numeric id for the secrets skill"

            with allure.step(
                "Step 10 — Repeat the wizard flow (Publish -> Preparation -> "
                "Continue) for the secrets skill"
            ):
                detail_page.navigate(secrets_skill_id)
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                secrets_response = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                secrets_body = secrets_response.json()

            with allure.step(
                "Step 11 — Verify the validation error indicates secrets/"
                "credentials were detected (AI-generated, source='ai', "
                "field='instructions')"
            ):
                assert secrets_body.get("status") == "FAIL", (
                    f"Expected status=FAIL for secrets content, got: {secrets_body!r}"
                )
                secrets_issues = secrets_body.get("critical_issues", [])
                secrets_hit = any(
                    entry.get("source") == "ai"
                    and entry.get("field") == "instructions"
                    and any(
                        phrase in (entry.get("issue") or "").lower()
                        for phrase in ("credential", "secret", "api key")
                    )
                    for entry in secrets_issues
                )
                assert secrets_hit, (
                    "Expected a critical_issues entry with source='ai', "
                    "field='instructions' referencing credentials/secrets, "
                    f"got: {secrets_issues!r}"
                )

            with allure.step('Step 12 — Verify the "Publish" button is disabled'):
                assert not detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be disabled "
                    "when status is FAIL"
                )
        finally:
            with allure.step("Cleanup — delete all three fixture skills"):
                for sid in skill_ids:
                    try:
                        skill_api.delete_skill(sid)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup skill {sid}: {cleanup_exc}")
