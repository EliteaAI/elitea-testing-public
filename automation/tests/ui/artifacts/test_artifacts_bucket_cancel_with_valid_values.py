"""UI Test for ELITEA-1815 — Save and Cancel Are Active with Valid Values, and
Cancel Does Not Create the Bucket.

The positive-form / Cancel branch, which no merged spec touches:
``test_artifacts_bucket_retention_edit_persistence.py`` (ELITEA-1810) cancels
the EDIT form and asserts no ``PUT``; ``test_artifacts_create_bucket_upload_file.py``
(ELITEA-1808) is the positive SAVE path. Nothing merged asserts "valid values
⇒ Save enabled" or "Cancel on the create form creates nothing".

Test flow (9 case steps, 1:1 with the AFS's Test Steps):
1. Navigate to Artifacts; assert the target name is ABSENT up front, so
   step 9's absence assertion is a real delta rather than a tautology about a
   name that was never free.
2. Open the New Bucket form — the route ``/artifacts/create-bucket`` is shared
   with the EDIT form (``CreateBucket.jsx:214`` switches the heading off
   ``currentBucket``), so the heading text is what proves it is the create
   form.
3-5. Fill a valid name and a valid retention policy, asserting each value
   actually CHANGED the form's defaults (``new-bucket`` / ``Years`` / ``1``) —
   a test that never moved the defaults would still satisfy a naive
   "value is present" read.
6. Both Save and Cancel are visible and enabled, and NO validation helper text
   is rendered — the absence of an error is the other half of "the form is in
   a valid state", and the exact mirror of ELITEA-1813.
7. Cancel closes the form and fires NO request at all.
8. The sidebar's Artifacts entry navigates to the Artifacts root.
9. ``bucket-cancel-test`` is absent — by direct row lookup, through the search
   filter, and by the step-7 capture having stayed empty.

Test data: the case's literal ``bucket-cancel-test`` is used verbatim rather
than a generated name — deliberately. The case's whole point is that this
exact name STAYS absent; a per-run generated name would weaken the assertion
into "a name nobody ever used is missing". Safe because nothing is ever
created (verified live: zero artifacts/buckets requests across the flow).

Fidelity: no substitution of any kind. Save is only ever ASSERTED on, never
clicked. ``capture_requests_matching`` is a passive listener, not a route
interception — nothing is fabricated, delayed, or injected.

Read-only by construction: the case creates nothing, so there is no seed and
no teardown, and this spec leaks no bucket into a project already carrying
~970 of them (#636).

AFS: test-specs/artifacts/l3_bucket-form-valid-values-cancel-no-bucket_ELITEA-1815.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p3: low priority (matches case priority "medium" / AFS l3)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_cancel_with_valid_values.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, rows
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
# The first /artifacts navigation of a fresh session renders ~970 bucket rows
# (#636) and has exceeded wait_for_page_load()'s 15s default — a condition
# wait with a bigger budget, never a sleep.
COLD_PAGE_LOAD_TIMEOUT = 60_000

# ---------------------------------------------------------------------------
# Test data — the case's own literals (see module docstring on why the name is
# NOT generated per run).
# ---------------------------------------------------------------------------
BUCKET_NAME = "bucket-cancel-test"
RETENTION_MEASURE = "days"          # option VALUE; the label is capitalized
RETENTION_MEASURE_LABEL = "Days"    # by SingleSelect's capitalizeFirstChar
RETENTION_VALUE = "3"

# Form defaults on a fresh create form — the baseline steps 3-5 must move.
DEFAULT_BUCKET_NAME = "new-bucket"
DEFAULT_RETENTION_MEASURE_LABEL = "Years"
DEFAULT_RETENTION_VALUE = "1"

# The single route /artifacts/create-bucket serves BOTH the create and edit
# forms; only the heading text discriminates them.
CREATE_FORM_HEADING = "New Bucket"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation — Cancel Path")
class TestArtifactBucketCancelWithValidValues:
    """ELITEA-1815 — with a valid name and retention policy both Save and
    Cancel are active, and clicking Cancel closes the form without creating
    the bucket."""

    @pytest.mark.p3
    @allure.title(
        "Save and Cancel are both active with valid values, and Cancel closes "
        "the New Bucket form without creating the bucket"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1815_save-and-cancel-buttons-active-with-valid-values.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_with_valid_values_creates_no_bucket(self, page):
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
                f"renders. Also verify {BUCKET_NAME!r} is ABSENT up front: "
                "step 9's absence assertion is meaningless if the name could "
                "already have been taken by a leftover"
            ):
                artifacts_page.navigate("/artifacts")
                artifacts_page.wait_for_page_load(timeout=COLD_PAGE_LOAD_TIMEOUT)
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )
                expect(artifacts_page.bucket_row(BUCKET_NAME)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click the create-bucket folder icon above the bucket "
                "list — the 'New Bucket' form opens. The URL is shared with the "
                "Edit form, so the heading text is the discriminating assertion"
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
                    "A fresh create form should pre-fill the Name field with "
                    f"{DEFAULT_BUCKET_NAME!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                f"Step 3 — Enter the valid bucket name {BUCKET_NAME!r} — the "
                "field accepts it verbatim, replacing the pre-filled default"
            ):
                artifacts_page.fill_bucket_name(BUCKET_NAME)
                assert artifacts_page.bucket_name_input.input_value() == BUCKET_NAME, (
                    f"The Name field should hold {BUCKET_NAME!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                f"Step 4 — Select the retention measure {RETENTION_MEASURE!r} "
                f"from the dropdown — the combobox reads "
                f"{RETENTION_MEASURE_LABEL!r} (moved off the "
                f"{DEFAULT_RETENTION_MEASURE_LABEL!r} default, which proves "
                "the selection actually took)"
            ):
                assert (
                    artifacts_page.get_retention_measure_text()
                    == DEFAULT_RETENTION_MEASURE_LABEL
                ), (
                    "A fresh create form should default the retention measure "
                    f"to {DEFAULT_RETENTION_MEASURE_LABEL!r}, got "
                    f"{artifacts_page.get_retention_measure_text()!r}"
                )
                artifacts_page.select_retention_measure(
                    RETENTION_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_retention_measure_combobox).to_have_text(
                    RETENTION_MEASURE_LABEL, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                f"Step 5 — Set the retention numerical field to "
                f"{RETENTION_VALUE!r} — the field shows it (and not the "
                f"{DEFAULT_RETENTION_VALUE!r} default, nor a concatenation of "
                "the two)"
            ):
                assert (
                    artifacts_page.get_retention_value() == DEFAULT_RETENTION_VALUE
                ), (
                    "A fresh create form should default the retention value to "
                    f"{DEFAULT_RETENTION_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )
                artifacts_page.set_retention_value(RETENTION_VALUE)
                assert artifacts_page.get_retention_value() == RETENTION_VALUE, (
                    f"The retention value field should hold {RETENTION_VALUE!r}, "
                    f"got {artifacts_page.get_retention_value()!r}"
                )

            with allure.step(
                "Step 6 — Verify both Save (highlighted/active) and Cancel are "
                "visible, active and clickable — and that NO validation helper "
                "text is rendered, which is what makes 'active' mean the form "
                "is VALID rather than merely rendered (the mirror of "
                "ELITEA-1813)"
            ):
                expect(artifacts_page.bucket_save_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_save_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_cancel_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_cancel_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_name_helper_text).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Arm a passive capture on any artifacts/buckets "
                "request, then click Cancel — the form closes, the app returns "
                "to the bare /artifacts root, and NO request fires at all "
                "(onCancel is a plain navigate(-1)). The network is the only "
                "oracle that can distinguish 'not created' from 'created but "
                "not yet rendered' on a ~970-row list, and it localises a "
                "Cancel regression here rather than at step 9"
            ):
                bucket_requests = artifacts_page.capture_requests_matching(
                    "artifacts/buckets"
                )
                artifacts_page.click_bucket_cancel_button(timeout=NAVIGATION_TIMEOUT)
                expect(artifacts_page.bucket_form_heading).to_have_count(
                    0, timeout=NAVIGATION_TIMEOUT
                )
                assert page.url.rstrip("/").endswith("/artifacts"), (
                    "Cancel should land on the bare Artifacts root, got "
                    f"{page.url!r}"
                )
                assert list(bucket_requests) == [], (
                    "Cancel must fire NO artifacts/buckets request at all — "
                    f"captured: {list(bucket_requests)!r}"
                )

            with allure.step(
                "Step 8 — Click 'Artifacts' in the left sidebar — navigation to "
                "the Artifacts root occurs with the bucket list rendered. "
                "Cancel already landed on /artifacts, so this is a same-route "
                "navigation: the assertion is that the case's own step keeps "
                "the app on a working Artifacts root"
            ):
                artifacts_page.sidebar_menu_item("artifacts").click()
                artifacts_page.wait_for_page_load(timeout=COLD_PAGE_LOAD_TIMEOUT)
                assert page.url.rstrip("/").endswith("/artifacts"), (
                    "The sidebar entry should navigate to the Artifacts root, "
                    f"got {page.url!r}"
                )

            with allure.step(
                f"Step 9 — Verify {BUCKET_NAME!r} does NOT appear in the bucket "
                "list. Asserted two independent ways — the direct row testid "
                "(a negative assertion on a huge list) and the bucket search "
                "filter, which narrows the list to whatever matches so 0 "
                "visible rows proves absence independently of rendering and "
                "scroll behaviour"
            ):
                expect(artifacts_page.bucket_row(BUCKET_NAME)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                artifacts_page.open_bucket_search(timeout=UI_ELEMENT_TIMEOUT)
                artifacts_page.search_buckets(BUCKET_NAME)
                expect(artifacts_page.all_bucket_rows()).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                artifacts_page.close_bucket_search(timeout=UI_ELEMENT_TIMEOUT)
                assert list(bucket_requests) == [], (
                    "No artifacts/buckets request may have fired at any point "
                    f"after Cancel either — captured: {list(bucket_requests)!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole valid-values + cancel flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the cancel-with-valid-"
                    f"values flow: {[m.text for m in console_errors]}"
                )
        finally:
            # The capture helper's own docstring warns that a leaked listener
            # can hang later tests — stop it whatever happened above.
            if bucket_requests is not None:
                bucket_requests.stop()
