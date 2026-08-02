"""UI Test for ELITEA-1811 / ELITEA-1814 — Bucket Name Validation Rejects
Invalid Name Formats (Family).

One parameterized spec covering both cases' identical flow against the SAME
yup validation rule (``^[a-zA-Z][a-zA-Z0-9-]*$``, ``CreateBucket.jsx``): open
the "New Bucket" form, type an invalid name, click Save, and verify the exact
inline validation error is shown, ``aria-invalid`` flips true, the Save button
stays enabled, no bucket-creation POST ever fires, and no bucket is created
or listed.

Parameter rows (one per source case/sub-case):
    1. ELITEA-1811        — "1bucket"      (starts with a digit)
    2. ELITEA-1814 (in 1) — "new-bucket$"  (disallowed special character)
    3. ELITEA-1814 (in 2) — "bucket_one"   (underscore not in allowed set)
    4. ELITEA-1814 (in 3) — "bucket one"   (space)

Each row is tagged with its originating case id (see
``INVALID_BUCKET_NAME_CASES``) so a single row's regression fails by itself
and never masks its healthy siblings.

AFS: test-specs/artifacts/l3_bucket-name-validation-invalid-name-formats_ELITEA-1811.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches both cases' "medium" priority / AFS l3)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_name_validation_invalid_formats.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p2]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # fields, buttons, helper text
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
NO_REQUEST_TIMEOUT = 5_000        # bounded wait proving NO creation POST fires
                                   # (yup blocks formik.handleSubmit client-side;
                                   # matches the AFS's own live-confirmed timeout)

EXPECTED_VALIDATION_ERROR = (
    "Name should start with a letter and contain only letters, numbers, and hyphen"
)

# One row per source case/sub-case — see module docstring.
INVALID_BUCKET_NAME_CASES = [
    pytest.param("ELITEA-1811", "1bucket", id="ELITEA-1811-leading-digit"),
    pytest.param("ELITEA-1814", "new-bucket$", id="ELITEA-1814-special-char"),
    pytest.param("ELITEA-1814", "bucket_one", id="ELITEA-1814-underscore"),
    pytest.param("ELITEA-1814", "bucket one", id="ELITEA-1814-space"),
]


@allure.epic("Artifacts")
@allure.feature("Bucket Creation — Name Validation")
class TestArtifactBucketNameValidationInvalidFormats:
    """ELITEA-1811/ELITEA-1814 — a bucket name that starts with a digit, or
    contains a disallowed special character/underscore/space, is rejected
    with the exact inline validation error; the Save button stays enabled;
    no creation POST ever fires; no bucket with that name is ever listed.
    """

    @pytest.mark.parametrize("case_id, invalid_name", INVALID_BUCKET_NAME_CASES)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1811_bucket-name-cannot-start-with-a-number.md",
        "onetest-ai Test Case link (ELITEA-1811)",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1814_bucket-name-rejects-non-alphanumeric-except-hyphen.md",
        "onetest-ai Test Case link (ELITEA-1814)",
    )
    @allure.title("Invalid bucket name format is rejected: {invalid_name!r}")
    @allure.severity(allure.severity_level.NORMAL)
    def test_bucket_name_validation_rejects_invalid_format(
        self, page, case_id, invalid_name,
    ):
        """Run once per Test Data row — ``case_id`` ties a failure back to
        its originating case (ELITEA-1811 or ELITEA-1814) so one row's
        regression never masks its healthy siblings.
        """
        artifacts_page = ArtifactsPage(page)

        with allure.step(f"[{case_id}] Step 1 — Navigate to Artifacts"):
            artifacts_page.navigate_to_artifacts()

        with allure.step(
            f"[{case_id}] Step 2 — Click '+ Artifact Bucket' — 'New Bucket' "
            f"form opens"
        ):
            artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
            assert "/artifacts/create-bucket" in artifacts_page.page.url, (
                f"[{case_id}] Expected URL to contain '/artifacts/create-bucket', "
                f"got: {artifacts_page.page.url!r}"
            )

        with allure.step(f"[{case_id}] Step 3 — Enter invalid name {invalid_name!r}"):
            artifacts_page.fill_bucket_name(invalid_name)
            assert artifacts_page.bucket_name_input.input_value() == invalid_name, (
                f"[{case_id}] Name field should accept {invalid_name!r} verbatim "
                f"(no client-side input masking/rejection)"
            )

        with allure.step(
            f"[{case_id}] Step 4 — Click Save — verify no bucket-creation POST "
            f"fires (client-side validation blocks submission entirely)"
        ):
            try:
                with page.expect_response(
                    lambda r: "artifacts/buckets" in r.url
                    and r.request.method == "POST",
                    timeout=NO_REQUEST_TIMEOUT,
                ):
                    artifacts_page.click_bucket_save_button_expect_no_request()
                pytest.fail(
                    f"[{case_id}] Unexpected POST .../artifacts/buckets fired "
                    f"for invalid name {invalid_name!r} — client-side "
                    f"validation should block the request entirely"
                )
            except PlaywrightTimeoutError:
                pass  # expected — yup blocks formik.onSubmit before any network call

        with allure.step(
            f"[{case_id}] Step 5 — Verify the inline validation error is shown, "
            f"the field is flagged invalid, and the Save button remains enabled"
        ):
            assert artifacts_page.is_bucket_name_invalid(timeout=UI_ELEMENT_TIMEOUT), (
                f"[{case_id}] Name field should be flagged aria-invalid=true "
                f"for {invalid_name!r}"
            )
            artifacts_page.bucket_name_helper_text.wait_for(
                state="visible", timeout=UI_ELEMENT_TIMEOUT
            )
            helper_text = (
                artifacts_page.bucket_name_helper_text.text_content() or ""
            ).strip()
            assert helper_text == EXPECTED_VALIDATION_ERROR, (
                f"[{case_id}] Expected validation message "
                f"{EXPECTED_VALIDATION_ERROR!r}, got: {helper_text!r}"
            )
            assert artifacts_page.bucket_save_button.is_enabled(), (
                f"[{case_id}] Save button should remain enabled/clickable "
                f"after the rejected Save attempt for {invalid_name!r}"
            )
            assert "/artifacts/create-bucket" in artifacts_page.page.url, (
                f"[{case_id}] A blocked Save must not navigate away from the "
                f"form, got URL: {artifacts_page.page.url!r}"
            )

        with allure.step(f"[{case_id}] Step 6 — Return to the Artifacts root"):
            artifacts_page.navigate_to_artifacts()
            assert artifacts_page.page.url.rstrip("/").endswith("/artifacts"), (
                f"[{case_id}] Expected URL to be the Artifacts root, got: "
                f"{artifacts_page.page.url!r}"
            )

        with allure.step(
            f"[{case_id}] Step 7 — Verify {invalid_name!r} does not appear in "
            f"the bucket list"
        ):
            assert not artifacts_page.bucket_exists(invalid_name, timeout=5000), (
                f"[{case_id}] Bucket {invalid_name!r} should NOT have been "
                f"created / should not appear in the bucket list"
            )
