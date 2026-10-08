"""UI Test for ELITEA-1805 — Artifacts Landing Page UI – Empty Bucket (No Files).

Regression test: verifies the Artifacts landing page's empty-bucket rendering
end to end — left-panel header (heading + create + search icons), the
storage-provider selector + bucket list, selecting the bucket (highlight +
left-panel tree label), the main-panel breadcrumb header, the absence of a
file table, the centered empty state (icon + message + Upload button), the
ABSENCE of the top-right toolbar actions (by design — issue #2394), the
left-panel footer bucket-count/size, and the retention/file-count tooltip on
the main-panel info icon (issue #1617).

Test flow:
0. Create a fresh, zero-file bucket via the UI "New Bucket" form
   (precondition — this case's own subject is the resulting EMPTY state,
   not bucket creation itself; mirrors ELITEA-1808's own setup pattern).
1. Navigate to the Artifacts section.
2. Verify the left-panel header: "Buckets" heading, create-bucket button,
   search-buckets button (and its stable aria-label).
3. Verify the storage-provider selector and at least one bucket row are
   visible under it.
4. Click the empty bucket's row — verify it becomes selected
   (`data-selected="true"`).
5. Verify the highlight persists and the left-panel tree's "No files in
   this bucket" sub-label appears — via the documented deliberate
   SECOND-click sequence (issue #2393: a bucket's first-ever selection
   does not auto-expand the tree; a second click on the now-active row
   does — NOT a retry loop).
6. Verify the main-panel breadcrumb header shows the bucket name.
7. Verify no file rows render in the main panel.
8. Verify the main-panel centered empty state (message + Upload button).
9. Verify the top-right toolbar actions (search/upload/download/delete) are
   ABSENT (unmounted, `.count() == 0`) for an empty bucket — the INVERSE of
   the case's literal wording, confirmed live by design (issue #2394).
10. Verify the left-panel footer shows the bucket count and a size string.
11. Hover the main-panel "Bucket info" icon — verify the retention-policy /
    file-count tooltip (issue #1617 — NOT a left-panel bucket-name hover,
    which shows nothing for a short name).

AFS: test-specs/artifacts/l3_landing-page-empty-bucket_ELITEA-1805.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority — AFS l3/"medium"; this
      folder's own l3→p2 convention, e.g. ELITEA-1809/1811)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_landing_page_ui.py -v
"""

import logging
import re
import time

import allure
import pytest

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # fields, buttons, rows, tooltip
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions, bucket-list refetch

# Confirmed live footer format (ELITEA-1805): "Buckets:1Size:0 B" — no
# separator between the two fields, no literal "MB" unit.
FOOTER_PATTERN = re.compile(r"Buckets:(\d+)Size:(.+)$")


def _generate_bucket_name(node_name: str) -> str:  # noqa: ARG001 — kept for call-site parity with ELITEA-1808's helper
    """Generate a unique, zero-file bucket name for this test's own setup.

    Reimplemented rather than using the shared ``artifact_bucket`` fixture
    (which some tests use with files already uploaded) — per the AFS, this
    case's "emptiness" is only guaranteed by the test's OWN fresh creation
    (reusing a shared bucket risks another test having uploaded a file into
    it between runs).

    **Deliberately SHORT** (unlike ELITEA-1808's own longer
    ``autotest-{node_name}-{ts}`` helper) — confirmed live during
    implementation: a long, timestamp-suffixed name overflows the
    left-panel row and triggers that panel's OWN conditional overflow
    tooltip (MUI ``Tooltip``), which then lingers as a SECOND open
    ``[role="tooltip"]`` and collides with Step 11's info-icon tooltip
    read (a Playwright strict-mode violation). The AFS's own bucket name
    (``elitea1805-empty``, 16 chars) never overflows — this generator
    stays in that same short range while remaining unique per run.
    """
    ts = str(int(time.time() * 1000))[-6:]
    return f"elitea1805-{ts}"


@allure.epic("Artifacts")
@allure.feature("Landing Page UI — Empty Bucket")
class TestArtifactsLandingPageUI:
    """ELITEA-1805 — Artifacts landing page's empty-bucket UI.

    The bucket is created BY the test's own setup (Step 0, a precondition —
    not one of the case's 11 numbered steps) and deleted in a manual
    teardown. No existing bucket is safely reusable for this case: its
    entire subject is the zero-file state, which only the test's own fresh
    bucket can guarantee for the full run.
    """

    @pytest.mark.tms("ELITEA-1805")
    @pytest.mark.p2
    @allure.title(
        "Artifacts landing page renders the correct empty-bucket UI"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1805_artifacts-landing-page-ui-empty-bucket.md",
        "onetest-ai Test Case link",
    )
    def test_landing_page_empty_bucket(self, page, artifact_api, request):
        """Verify the Artifacts landing page's empty-bucket UI end to end.

        A fresh, zero-file bucket is created in setup (Step 0) — the
        minimal state this observable inherently requires (workflow skill
        Hard Rule 10): emptiness can only be guaranteed by a bucket this
        test itself just created, never a shared/reused one.
        """
        bucket_name = _generate_bucket_name(request.node.name)

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)

        try:
            with allure.step(
                "Step 0 (setup) — Create a fresh, zero-file bucket via the "
                "'New Bucket' form"
            ):
                artifacts_page.navigate_to_artifacts()
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                artifacts_page.fill_bucket_name(bucket_name)
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got: "
                    f"{create_response.status} for {create_response.url}"
                )
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step("Step 1 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()
                assert artifacts_page.buckets_heading.is_visible(), (
                    "'Buckets' heading should be visible on the Artifacts "
                    "landing page"
                )

            with allure.step(
                "Step 2 — Verify the left-panel header: 'Buckets' label, "
                "create-bucket (folder) icon, and search icon"
            ):
                assert (
                    artifacts_page.buckets_heading.text_content() or ""
                ) == "Buckets", (
                    "Left-panel heading text should read 'Buckets' (DOM "
                    "text; the case's 'BUCKETS' describes the CSS "
                    "text-transform, not the literal content)"
                )
                assert artifacts_page.create_bucket_button.is_visible(), (
                    "Create-bucket button (the case's 'folder icon') "
                    "should be visible in the left-panel header"
                )
                assert artifacts_page.search_buckets_button.is_visible(), (
                    "Search-buckets button (the case's 'search icon') "
                    "should be visible in the left-panel header"
                )
                assert (
                    artifacts_page.search_buckets_button.get_attribute("aria-label")
                    == "Search buckets"
                ), "Search-buckets button should carry aria-label='Search buckets'"

            with allure.step(
                "Step 3 — Verify the bucket list is visible under the "
                "storage-provider selector"
            ):
                assert artifacts_page.storage_selector.is_visible(), (
                    "Storage-provider selector should be visible above the "
                    "bucket list"
                )
                assert "Storage:" in (
                    artifacts_page.storage_selector.text_content() or ""
                ), "Storage-provider selector should show a 'Storage:' label"
                assert artifacts_page.get_visible_bucket_count() >= 1, (
                    "At least one bucket row should be visible beneath the "
                    "storage-provider selector"
                )

            with allure.step(
                "Step 4 — Click the empty bucket's row — verify it becomes "
                "selected"
            ):
                artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                assert artifacts_page.is_bucket_selected(
                    bucket_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Bucket row '{bucket_name}' should carry data-selected='true'"

            with allure.step(
                "Step 5 — Verify the bucket stays highlighted and the "
                "left-panel tree shows 'No files in this bucket' — via the "
                "documented deliberate second-click sequence (issue #2393: "
                "a bucket's FIRST-EVER selection does not auto-expand the "
                "tree; a second click on the now-active row does)"
            ):
                assert artifacts_page.is_bucket_selected(
                    bucket_name, timeout=UI_ELEMENT_TIMEOUT,
                ), f"Bucket row '{bucket_name}' should still be highlighted"
                artifacts_page.expand_bucket_tree_if_needed(
                    bucket_name, timeout=UI_ELEMENT_TIMEOUT,
                )
                tree_label = artifacts_page.get_bucket_tree_empty_state(bucket_name)
                assert (tree_label.text_content() or "").strip() == (
                    "No files in this bucket"
                ), "Left-panel tree sub-label should read 'No files in this bucket'"

            with allure.step(
                "Step 6 — Verify the main-panel header shows the bucket name"
            ):
                assert (
                    artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT)
                    == bucket_name
                ), "Main-panel breadcrumb should show the selected bucket's name"

            with allure.step(
                "Step 7 — Verify no file table / file rows render in the "
                "main panel"
            ):
                assert artifacts_page.get_file_row_count() == 0, (
                    "No file rows should render for a zero-file bucket"
                )

            with allure.step(
                "Step 8 — Verify the main-panel centered empty state: "
                "message and 'Upload files' button (icon verified visually "
                "during analysis — no accessible/stable DOM handle exists "
                "for it, see the AFS's Concrete Handles table)"
            ):
                assert artifacts_page.is_bucket_empty(timeout=UI_ELEMENT_TIMEOUT), (
                    "Main-panel empty-state label should be visible"
                )
                assert (artifacts_page.empty_state_label.text_content() or "").strip() == (
                    "No files in this bucket"
                ), "Main-panel empty-state message should read 'No files in this bucket'"
                assert artifacts_page.upload_files_empty_state_button.is_visible(), (
                    "Centered 'Upload files' button should be visible in "
                    "the empty state"
                )

            with allure.step(
                "Step 9 — CONFIRMED CASE-TEXT DIVERGENCE (issue #2394): for "
                "an empty bucket, the top-right toolbar search/upload/"
                "download/delete icons are intentionally ABSENT "
                "(unmounted), not merely disabled — assert the OPPOSITE of "
                "the case's literal wording"
            ):
                assert artifacts_page.file_search_input.count() == 0, (
                    "Toolbar search input should not be mounted for an "
                    "empty bucket (issue #2394)"
                )
                assert artifacts_page.upload_files_button.count() == 0, (
                    "Toolbar upload button should not be mounted for an "
                    "empty bucket (issue #2394)"
                )
                assert artifacts_page.download_files_button.count() == 0, (
                    "Toolbar download button should not be mounted for an "
                    "empty bucket (issue #2394)"
                )
                assert artifacts_page.delete_files_button.count() == 0, (
                    "Toolbar delete button should not be mounted for an "
                    "empty bucket (issue #2394)"
                )

            with allure.step(
                "Step 10 — Verify the left-panel footer shows the correct "
                "bucket count and a size string"
            ):
                footer_text = artifacts_page.get_bucket_footer_text(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                match = FOOTER_PATTERN.search(footer_text)
                assert match, (
                    f"Footer text should match 'Buckets:<N>Size:<X>', got: "
                    f"{footer_text!r}"
                )
                bucket_count = int(match.group(1))
                size_text = match.group(2).strip()
                assert bucket_count >= 1, (
                    f"Footer bucket count should be at least 1 (the bucket "
                    f"this test created), got: {bucket_count}"
                )
                assert size_text, "Footer size string should be non-empty"

            with allure.step(
                "Step 11 — Hover the main-panel 'Bucket info' icon — "
                "verify the retention-policy / file-count tooltip (issue "
                "#1617: the real location is the main-panel info icon, NOT "
                "a left-panel bucket-name hover, which shows nothing for a "
                "short name)"
            ):
                artifacts_page.hover_bucket_info_button(timeout=UI_ELEMENT_TIMEOUT)
                tooltip_text = artifacts_page.get_bucket_info_tooltip_text(
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "Retention Policy" in tooltip_text, (
                    f"Tooltip should mention 'Retention Policy', got: "
                    f"{tooltip_text!r}"
                )
                assert "1 Year" in tooltip_text, (
                    f"Tooltip should show the default retention '1 Year', "
                    f"got: {tooltip_text!r}"
                )
                assert "Number of files" in tooltip_text, (
                    f"Tooltip should mention 'Number of files', got: "
                    f"{tooltip_text!r}"
                )
                assert re.search(r"Number of files:?\s*0", tooltip_text), (
                    f"Tooltip should show a file count of 0 for the empty "
                    f"bucket, got: {tooltip_text!r}"
                )

            with allure.step(
                "Side-channel check — no console errors across the full "
                "create → select → toggle-expand → hover flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the empty-bucket "
                    f"landing-page flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Cleanup — known pre-existing defect (#636, already filed, not
            # new to this case): delete_bucket() 404s on this DEV
            # environment, so the bucket will likely leak. Do not treat
            # "the delete call ran" as proof the bucket is gone — out of
            # scope to fix here (AFS § Cleanup). Never let this failure
            # mask the test's own pass/fail.
            try:
                artifact_api.delete_bucket(bucket_name)
                logger.info("Deleted artifact bucket '%s'", bucket_name)
            except Exception as exc:
                logger.warning(
                    "Failed to delete artifact bucket '%s' (known defect "
                    "#636 — delete 404s in dev): %s", bucket_name, exc,
                )
