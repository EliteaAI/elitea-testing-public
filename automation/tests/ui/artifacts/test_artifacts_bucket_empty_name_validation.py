"""UI Test for ELITEA-1813 — A Bucket Cannot Be Created with an Empty Name
Field.

The empty-name branch of the New Bucket form's validation, which no merged
spec touches: ``test_artifacts_bucket_name_validation_invalid_formats.py``
(ELITEA-1811/1814) covers the *non-empty invalid* branch and explicitly
asserts the OPPOSITE Save state (``bucket_save_button.is_enabled()``), and
``test_artifacts_bucket_retention_edit_persistence.py`` (ELITEA-1810) cancels
the *edit* form. Neither asserts a disabled Save nor the ``Name is required``
message.

Test flow (9 case steps, 1:1 with the AFS's Test Steps):
1. Navigate to Artifacts; capture the bucket-row count as the step-9 baseline.
2. Open the New Bucket form — the route ``/artifacts/create-bucket`` is shared
   with the EDIT form (``CreateBucket.jsx:214`` switches the heading off
   ``currentBucket``), so the heading text is what proves it is the create
   form. Also asserts Save is ENABLED here, so step 4's flip is provably
   caused by the clear and not by a permanently-disabled button.
3. Clear the pre-filled ``new-bucket`` default.
4. Save is disabled AND the click is genuinely refused — the case says both
   ("disabled / not clickable"); a ``disabled`` attribute alone does not
   prove the click is refused.
5. The inline ``Name is required`` message, after an explicit blur.
6. Cancel is visible and enabled.
7-8. Cancel closes the form and returns to the bare ``/artifacts`` root.
9. The bucket list is back and NOTHING was created — asserted three ways.

Case-text divergence asserted as the LIVE contract (reverse-masking guard):
- Case step 5 asserts the ``Name is required`` message immediately after the
  clear, but ``CreateBucket.jsx:243-244`` gates both ``error`` and
  ``helperText`` on ``formik.touched.name``, which Formik sets on BLUR or
  SUBMIT — and the submit path is unreachable here because Save is disabled
  while the name is empty. This is correct standard MUI/Formik behaviour, not
  a defect, so the spec adds an explicit blur AND pins the pre-blur state
  (helper text absent, ``aria-invalid="false"``) so a future move to
  validate-on-change fails loudly instead of being papered over. Filed as
  case-text CLARIFICATION #1680.

Fidelity: no substitution of any kind. Every observable — the disabled Save,
the refused click, the helper text, the absence of a creation request — is
produced by the live system. ``capture_requests_matching`` is a passive
listener, not a route interception: nothing is fabricated, delayed, or
injected.

Read-only by construction: the case creates nothing, so there is no seed and
no teardown, and this spec leaks no bucket into a project already carrying
~970 of them (#636).

AFS: test-specs/artifacts/l3_bucket-empty-name-save-disabled-cancel_ELITEA-1813.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p3: low priority (matches case priority "medium" / AFS l3)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_empty_name_validation.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, helper text
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
# The first /artifacts navigation of a fresh session renders ~970 bucket rows
# (#636) and has exceeded wait_for_page_load()'s 15s default — a condition
# wait with a bigger budget, never a sleep.
COLD_PAGE_LOAD_TIMEOUT = 60_000
# Bounded wait proving the disabled Save genuinely refuses the click:
# Playwright retries actionability until this elapses, then raises.
DISABLED_CLICK_TIMEOUT = 2_000

# The form's own pre-filled default (CreateBucket.jsx initialValues.name) and
# the only name that could plausibly have been submitted from this flow.
DEFAULT_BUCKET_NAME = "new-bucket"

# yup: .required('Name is required') — confirmed live, byte-exact.
EXPECTED_EMPTY_NAME_MESSAGE = "Name is required"

# The single route /artifacts/create-bucket serves BOTH the create and edit
# forms; only the heading text discriminates them.
CREATE_FORM_HEADING = "New Bucket"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation — Name Validation")
class TestArtifactBucketEmptyNameValidation:
    """ELITEA-1813 — with the Name field empty the Save button is disabled and
    un-clickable, the ``Name is required`` message is shown once the field is
    blurred, and Cancel closes the form without creating anything."""

    @pytest.mark.p3
    @allure.title(
        "An empty bucket Name disables Save, shows 'Name is required', and "
        "Cancel closes the form without creating a bucket"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1813_bucket-cannot-be-created-with-empty-name-field.md",
        "onetest-ai Test Case link",
    )
    def test_empty_bucket_name_disables_save_and_cancel_creates_nothing(self, page):
        """Drive the case's 9 steps end-to-end against the live system."""
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)
        bucket_requests = None

        try:
            with allure.step(
                "Step 1 — Navigate to the Artifacts section — the bucket list "
                "renders; capture its row count as the step-9 baseline"
            ):
                artifacts_page.navigate("/artifacts")
                artifacts_page.wait_for_page_load(timeout=COLD_PAGE_LOAD_TIMEOUT)
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )
                baseline_row_count = artifacts_page.get_visible_bucket_count()
                assert baseline_row_count > 0, (
                    "Expected the bucket list to render at least one row before "
                    "the flow starts — the step-9 'row count unchanged' "
                    "assertion is meaningless against an empty baseline"
                )
                logger.info("Baseline bucket-row count: %d", baseline_row_count)

            with allure.step(
                "Step 2 — Click the create-bucket folder icon above the bucket "
                "list — the 'New Bucket' form opens. The URL is shared with the "
                "Edit form, so the heading text is the discriminating "
                "assertion. Save is ENABLED here: the baseline that proves "
                "step 4's flip is caused by the clear"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {page.url!r}"
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == CREATE_FORM_HEADING
                ), (
                    f"The form should be headed {CREATE_FORM_HEADING!r} — the "
                    "route is shared with the Edit form "
                    "(CreateBucket.jsx:214 switches the heading off "
                    "`currentBucket`), so the URL alone cannot prove the "
                    "case's \"'New Bucket' form opens\""
                )
                assert (
                    artifacts_page.bucket_name_input.input_value()
                    == DEFAULT_BUCKET_NAME
                ), (
                    f"A fresh create form should pre-fill the Name field with "
                    f"{DEFAULT_BUCKET_NAME!r} (the case's own Test Data), got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )
                expect(artifacts_page.bucket_save_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                f"Step 3 — Delete the Name field's default {DEFAULT_BUCKET_NAME!r} "
                "— the field is cleared and empty"
            ):
                artifacts_page.clear_bucket_name()
                assert artifacts_page.bucket_name_input.input_value() == "", (
                    "The Name field should be empty after the clear, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                "Step 4 — Verify the Save button is disabled AND that the click "
                "is genuinely refused. The case claims both ('disabled / not "
                "clickable'); the `disabled` attribute alone does not prove "
                "the click is refused"
            ):
                expect(artifacts_page.bucket_save_button).to_be_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                with pytest.raises(PlaywrightTimeoutError):
                    # Playwright waits for actionability and gives up with
                    # "element is not enabled" — the honest proof that the
                    # click cannot land. click_bucket_save_button() is
                    # deliberately NOT used: it wraps expect_response on a POST
                    # that can never fire here and would hang instead.
                    artifacts_page.bucket_save_button.click(
                        timeout=DISABLED_CLICK_TIMEOUT
                    )

            with allure.step(
                "Step 5 — Verify the inline 'Name is required' message. The "
                "PRE-blur state is asserted first (helper text absent, "
                "aria-invalid=false): CreateBucket.jsx:243-244 gates both on "
                "formik.touched.name, so the message appears only once the "
                "field is blurred — the case text omits that blur "
                "(CLARIFICATION #1680). Pinning the pre-blur contract makes a "
                "future move to validate-on-change fail loudly instead of "
                "being silently papered over by the blur"
            ):
                expect(artifacts_page.bucket_name_helper_text).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not artifacts_page.is_bucket_name_invalid(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "Before the field is blurred the Name input should NOT be "
                    "flagged aria-invalid — formik.touched.name is still false"
                )

                artifacts_page.bucket_name_input.press("Tab")

                expect(artifacts_page.bucket_name_helper_text).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                helper_text = (
                    artifacts_page.bucket_name_helper_text.text_content() or ""
                ).strip()
                assert helper_text == EXPECTED_EMPTY_NAME_MESSAGE, (
                    f"Expected the inline validation message "
                    f"{EXPECTED_EMPTY_NAME_MESSAGE!r}, got {helper_text!r}"
                )
                assert artifacts_page.is_bucket_name_invalid(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "The Name field should be flagged aria-invalid=true once "
                    "the empty value has been touched"
                )
                expect(artifacts_page.bucket_save_button).to_be_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Verify the Cancel button is visible, active and "
                "clickable"
            ):
                expect(artifacts_page.bucket_cancel_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_cancel_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Arm a passive capture on any artifacts/buckets "
                "request, then click Cancel — the form closes"
            ):
                bucket_requests = artifacts_page.capture_requests_matching(
                    "artifacts/buckets"
                )
                artifacts_page.click_bucket_cancel_button(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 8 — Verify the bucket-creation page is closed: neither "
                "the form heading nor the Name field remains, and the app is "
                "back on the bare /artifacts root"
            ):
                expect(artifacts_page.bucket_form_heading).to_have_count(
                    0, timeout=NAVIGATION_TIMEOUT
                )
                expect(artifacts_page.bucket_name_input).to_have_count(
                    0, timeout=NAVIGATION_TIMEOUT
                )
                assert page.url.rstrip("/").endswith("/artifacts"), (
                    "Cancel (a plain navigate(-1)) should land on the bare "
                    f"Artifacts root, got {page.url!r}"
                )

            with allure.step(
                "Step 9 — Verify the bucket list is displayed again and NO "
                "bucket was created. Asserted three ways: no artifacts/buckets "
                "request ever fired (the network is the only oracle that can "
                "distinguish 'not created' from 'created but not yet rendered' "
                "on a ~970-row list), no row keyed by the default name exists, "
                "and the rendered row count is unchanged from the step-1 "
                "baseline (which also catches a creation under any OTHER name)"
            ):
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert list(bucket_requests) == [], (
                    "Cancel must fire NO artifacts/buckets request at all — "
                    f"captured: {list(bucket_requests)!r}"
                )
                expect(
                    artifacts_page.bucket_row(DEFAULT_BUCKET_NAME)
                ).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                expect(artifacts_page.all_bucket_rows()).to_have_count(
                    baseline_row_count, timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole validation + cancel flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the empty-name "
                    f"validation flow: {[m.text for m in console_errors]}"
                )
        finally:
            # The capture helper's own docstring warns that a leaked listener
            # can hang later tests — stop it whatever happened above.
            if bucket_requests is not None:
                bucket_requests.stop()
