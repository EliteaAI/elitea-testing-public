"""UI Test for ELITEA-1809 — Duplicate Bucket Name Is Not Allowed.

Regression test: verifies that attempting to create a bucket with a name
that collides with an existing bucket is rejected with a 400 response and
the server-generated error message, that the "New Bucket" form stays open
(no navigation away), and that no duplicate bucket is created. Also
exercises the left-panel bucket-search feature (icon -> input with a
"Search buckets" tooltip -> 300ms-debounced client-side filter -> clear)
both before and after the duplicate-creation attempt.

Test flow:
0. Precondition (not a numbered case step) — create a bucket via the "New
   Bucket" form. The generated name contains "buck" (the case's own search
   keyword) so it participates in the later search steps.
1. Navigate to Artifacts.
2-3. Open bucket search — verify the input appears and the search-icon
   button's tooltip text ("Search buckets") via its static aria-label.
4-6. Type "buck" — verify the input value, that the rendered bucket list
   narrows, and that the precondition bucket is present in the filtered
   results.
7. Clear/close search — verify the full (unfiltered) list is restored.
8-11. Open the "New Bucket" form again, verify its defaults, and enter the
   SAME name as the precondition bucket, leaving Retention at its default.
12. Click Save — verifies the creation POST returns 400 with the
   server-generated "Bucket with name {name} already exists" body.
13. Verify the red error toast shows that exact message.
14. Verify the form remains open (no navigation), with the duplicate name
    still in the field.
15. Return to the Artifacts root (via direct navigation — see the
    Automation Hints amendment in the AFS for why the literal sidebar click
    isn't automated here).
16-18. Search "buck" again — verify the precondition bucket still appears
    exactly once, and that the filtered result count is unchanged from the
    first search pass (steps 4-6) — proof that the failed attempt created
    zero new buckets.

AFS: test-specs/artifacts/l3_duplicate-bucket-name-not-allowed_ELITEA-1809.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority — AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_duplicate_bucket_name.py -v
"""

import logging
import time

import allure
import pytest

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # fields, buttons, search input
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions, bucket-list refetch
TOAST_TIMEOUT = 5_000             # toast has a ~3s auto-dismiss window — wait
                                   # for visible, never assert continued presence

# Browser's own automatic network-layer log for the intentionally-triggered
# 400 (e.g. "Failed to load resource: the server responded with a status of
# 400 (Bad Request) @ ...") — expected for this negative-path case, not an
# application-level error. Filtered out of the console-error check below.
EXPECTED_CONSOLE_ERROR_SUBSTRING = "Failed to load resource"


def _generate_duplicate_test_bucket_name() -> str:
    """Generate a unique bucket name containing "buck" (the case's own
    search keyword, used in Test Steps 4-6/16-18) — this project's generic
    ``_generate_bucket_name(node_name)`` helper (ELITEA-1808's pattern) does
    not guarantee a "buck" substring depending on the test's own node name,
    so a case-specific generator is used instead.
    """
    ts = str(int(time.time() * 1000))[-6:]
    return f"autotest-buck1-{ts}"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation — Duplicate Name Validation")
class TestArtifactDuplicateBucketName:
    """ELITEA-1809 — Creating a bucket with a name that collides with an
    existing bucket is rejected; the form stays open; no duplicate bucket
    is created. Also covers the left-panel bucket-search feature used
    before and after the duplicate-creation attempt.
    """

    @pytest.mark.p2
    @allure.title("Duplicate bucket name is rejected; no duplicate is created")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1809_duplicate-bucket-name-is-not-allowed.md",
        "onetest-ai Test Case link",
    )
    def test_duplicate_bucket_name_is_not_allowed(self, page, artifact_api):
        """Attempting to create a bucket with a colliding name is rejected.

        The precondition bucket is a genuine mutation the observable
        requires (workflow skill Hard Rule 10: the case's own subject is
        "does the system reject a name that collides with something real",
        so a real collision target must exist) — created via the SAME "New
        Bucket" UI form the duplicate-attempt itself uses, keeping both
        creations on the identical code path the case exercises (not the
        ``artifact_bucket`` API fixture).
        """
        bucket_name = _generate_duplicate_test_bucket_name()

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)

        try:
            # Precondition setup (not a numbered case step) — create the
            # collision-target bucket via the "New Bucket" form.
            artifacts_page.navigate_to_artifacts()
            artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
            artifacts_page.fill_bucket_name(bucket_name)
            precondition_response = artifacts_page.click_bucket_save_button(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert precondition_response.status == 200, (
                f"Precondition bucket creation POST should return 200, got: "
                f"{precondition_response.status} for {precondition_response.url}"
            )
            artifacts_page.wait_for_bucket_in_list(bucket_name, timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 1 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()
                baseline_bucket_count = artifacts_page.get_visible_bucket_count()
                assert baseline_bucket_count >= 1, (
                    "Expected at least the just-created precondition bucket "
                    "to be visible in the (unfiltered) bucket list"
                )

            with allure.step(
                "Steps 2-3 — Click the search icon — verify the search input "
                "opens and its tooltip text is 'Search buckets'"
            ):
                artifacts_page.open_bucket_search(timeout=UI_ELEMENT_TIMEOUT)
                assert (
                    artifacts_page.search_buckets_button.get_attribute("aria-label")
                    == "Search buckets"
                ), "Search button's tooltip (surfaced as a static aria-label) should read 'Search buckets'"

            with allure.step(
                "Steps 4-6 — Type 'buck' — verify the input reflects it, the "
                "rendered bucket list narrows, and the precondition bucket "
                "is present in the filtered results"
            ):
                artifacts_page.search_buckets("buck")
                assert artifacts_page.bucket_search_input.input_value() == "buck", (
                    "Search input should display the typed query 'buck'"
                )
                first_pass_filtered_count = artifacts_page.get_visible_bucket_count()
                assert first_pass_filtered_count < baseline_bucket_count, (
                    f"Filtering by 'buck' should narrow the rendered bucket "
                    f"list below the unfiltered baseline of "
                    f"{baseline_bucket_count}, got {first_pass_filtered_count}"
                )
                assert artifacts_page.count_bucket_rows(bucket_name) == 1, (
                    f"Precondition bucket {bucket_name!r} should be present "
                    f"exactly once in the 'buck'-filtered results"
                )

            with allure.step(
                "Step 7 — Clear the search field and close the search box — "
                "verify the full (unfiltered) bucket list is restored"
            ):
                artifacts_page.close_bucket_search(timeout=UI_ELEMENT_TIMEOUT)
                assert artifacts_page.get_visible_bucket_count() == baseline_bucket_count, (
                    "Closing search should restore the full unfiltered "
                    f"bucket list ({baseline_bucket_count} buckets)"
                )

            with allure.step(
                "Step 8 — Click the '+ Artifact Bucket' button — verify it "
                "opens the 'New Bucket' form as a full page"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in artifacts_page.page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {artifacts_page.page.url!r}"
                )

            with allure.step(
                "Step 9 — Verify the 'New Bucket' form is visible with all "
                "required fields, pre-filled with their defaults"
            ):
                assert artifacts_page.bucket_name_input.input_value() == "new-bucket", (
                    "Name field should be pre-filled with the literal default "
                    "'new-bucket' on a fresh form load"
                )
                assert (
                    artifacts_page.bucket_retention_measure_combobox.text_content() or ""
                ).strip() == "Years", "Retention measure should default to 'Years'"
                assert artifacts_page.bucket_retention_value_input.input_value() == "1", (
                    "Retention value should default to '1'"
                )
                assert artifacts_page.bucket_save_button.is_visible(), (
                    "Save button should be visible on the 'New Bucket' form"
                )

            with allure.step(
                "Step 10 — Enter the SAME name as the precondition bucket — "
                "verify the field displays it exactly"
            ):
                artifacts_page.fill_bucket_name(bucket_name)
                assert artifacts_page.bucket_name_input.input_value() == bucket_name, (
                    f"Name field should show the duplicate name {bucket_name!r} "
                    f"after filling"
                )

            with allure.step(
                "Step 11 — Leave Retention policy as default — verify it is "
                "still Years/1 after filling the name"
            ):
                assert (
                    artifacts_page.bucket_retention_measure_combobox.text_content() or ""
                ).strip() == "Years", "Retention measure should remain 'Years'"
                assert artifacts_page.bucket_retention_value_input.input_value() == "1", (
                    "Retention value should remain '1'"
                )

            with allure.step(
                "Step 12 — Click Save — verify the creation POST is rejected "
                "with 400 and the server-generated duplicate-name message"
            ):
                duplicate_response = artifacts_page.click_bucket_save_button(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert duplicate_response.status == 400, (
                    f"Duplicate-name bucket creation POST should return 400, "
                    f"got: {duplicate_response.status} for {duplicate_response.url}"
                )
                expected_message = f"Bucket with name {bucket_name} already exists"
                body = duplicate_response.json()
                assert body.get("message") == expected_message, (
                    f"400 response body should carry the exact duplicate-name "
                    f"message, got: {body!r}"
                )

            with allure.step(
                "Step 13 — Verify the red error notification shows the exact "
                "duplicate-name message"
            ):
                artifacts_page.success_toast_message.wait_for(
                    state="visible", timeout=TOAST_TIMEOUT,
                )
                toast_text = (artifacts_page.success_toast_message.text_content() or "").strip()
                assert toast_text == expected_message, (
                    f"Error toast should show {expected_message!r}, got: "
                    f"{toast_text!r}"
                )

            with allure.step(
                "Step 14 — Verify the 'New Bucket' form remains open (no "
                "navigation), with the duplicate name still in the field"
            ):
                assert "/artifacts/create-bucket" in artifacts_page.page.url, (
                    f"A failed Save must not navigate away from the form, "
                    f"got URL: {artifacts_page.page.url!r}"
                )
                assert artifacts_page.bucket_name_input.is_visible(), (
                    "Name field should still be visible after the failed Save"
                )
                assert artifacts_page.bucket_save_button.is_visible(), (
                    "Save button should still be visible after the failed Save"
                )
                assert artifacts_page.bucket_name_input.input_value() == bucket_name, (
                    "Name field should still contain the (unchanged, still "
                    "duplicate) name after the failed Save"
                )

            with allure.step(
                "Step 15 — Return to the Artifacts root — verify the URL "
                "reflects it"
            ):
                # AFS amendment (declared per role-overrides.md's
                # declared-improvisation protocol): the case's literal
                # "click Artifacts in the left sidebar" has no testid on the
                # shared SidebarMenuItem/SidebarBody.jsx component, which
                # renders EVERY sidebar nav entry (Chat, Agents, Skills,
                # Pipelines, ...) — threading a feature-scoped testid there
                # is a broad, high-blast-radius shared-component change no
                # other case step touches. navigate_to_artifacts() reaches
                # the identical observable (URL becomes /artifacts) via the
                # SAME mechanism the case's own Step 1 already uses.
                artifacts_page.navigate_to_artifacts()
                assert artifacts_page.page.url.rstrip("/").endswith("/artifacts"), (
                    f"Expected URL to be the Artifacts root, got: "
                    f"{artifacts_page.page.url!r}"
                )

            with allure.step(
                "Steps 16-18 — Search 'buck' again — verify the precondition "
                "bucket appears exactly once (no duplicate created) and the "
                "filtered result count is unchanged from the first search pass"
            ):
                artifacts_page.open_bucket_search(timeout=UI_ELEMENT_TIMEOUT)
                artifacts_page.search_buckets("buck")
                # PRIMARY, testid-only proof: a real duplicate bucket, if one
                # had been created, would render a SECOND DOM element sharing
                # the identical dynamic testid string.
                assert artifacts_page.count_bucket_rows(bucket_name) == 1, (
                    f"Exactly one row for {bucket_name!r} should be present "
                    f"in the 'buck'-filtered results — a count other than 1 "
                    f"means either a duplicate was created or the "
                    f"precondition bucket vanished"
                )
                # SECONDARY proof: the filtered list's total size is
                # unchanged from the first search pass (Steps 4-6) — an
                # independent, testid-based, environment-count-agnostic
                # signal that no OTHER new "buck"-matching bucket appeared
                # either.
                second_pass_filtered_count = artifacts_page.get_visible_bucket_count()
                assert second_pass_filtered_count == first_pass_filtered_count, (
                    f"'buck'-filtered bucket count should be unchanged "
                    f"across the failed duplicate-creation attempt: before="
                    f"{first_pass_filtered_count}, after={second_pass_filtered_count}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across "
                "the search -> duplicate-attempt -> search flow (the "
                "browser's own 'Failed to load resource: 400' log for the "
                "intentionally-triggered 400 is expected and excluded)"
            ):
                unexpected_console_errors = [
                    m for m in console_errors
                    if EXPECTED_CONSOLE_ERROR_SUBSTRING not in (m.text or "")
                ]
                assert not unexpected_console_errors, (
                    "Unexpected console errors during the duplicate-bucket "
                    f"flow: {[m.text for m in unexpected_console_errors]}"
                )
        finally:
            # Cleanup — known pre-existing defect (#636, already filed, not
            # new to this case): delete_bucket() 404s on both URL-format
            # attempts in the current dev environment, so the bucket will
            # likely leak. Do not treat "the delete call ran" as proof the
            # bucket is gone — out of scope to fix here (AFS § Cleanup).
            try:
                artifact_api.delete_bucket(bucket_name)
                logger.info("Deleted artifact bucket '%s'", bucket_name)
            except Exception as exc:
                logger.warning(
                    "Failed to delete artifact bucket '%s' (known defect "
                    "#636 — delete 404s in dev): %s", bucket_name, exc,
                )
