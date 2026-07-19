"""UI Test for ELITEA-1868 — Cancel During Artifact Toolkit Creation Does Not
Create a Toolkit or a Bucket.

Regression test: drives the full "New Toolkit" wizard through the type-picker
(search "art" -> filter to the sole "Artifact" card under STORAGE), fills the
Artifact form's Name/Bucket fields, then confirms Cancel via the "Warning"
dialog's "Discard" button — and verifies that confirming Cancel creates
NEITHER a toolkit NOR a bucket, at both the UI level (name-scoped searches on
the Toolkits list and the Artifacts bucket panel, count == baseline captured
at test start) and the network level (no POST ever fires to the
toolkit-create or bucket-create endpoints across the whole flow).

Known defect (github.com/EliteaAI/elitea-testing-public#655, MAJOR,
isolated): confirming Cancel does NOT navigate back to the Toolkits list as
the case's own step 12 requires — the app falls back to the "Choose the
toolkit type" picker at the SAME URL instead
(``CreateToolkitToolTabBar.jsx``'s cancel path only clears local form state
and never calls ``navigate()``, unlike the Save-success path a few lines
below in the same file). This is an ISOLATED defect — the case's actual
namesake objective ("no toolkit/bucket created") holds true independently of
where Cancel lands the user — asserted with ``expect.soft()`` against the
case's documented CORRECT expected value (the Toolkits list URL) per this
project's no-masking policy (sanctioned-RED exception,
``.agents/testing.md`` § Merge gate).

A second, unrelated MINOR defect (github.com/EliteaAI/elitea-testing-public#656
— a React "unique key prop" console warning that fires on every load of the
type-picker screen) is filed separately and is explicitly NOT gating; it is
excluded from this test's console-error check by its exact filed signature
(never a blanket warning suppression) so a genuinely new console error would
still fail the test.

Test flow:
1. Navigate to the Toolkits list; verify toolkit cards are present. Capture
   the baseline count of any "cancelled-toolkit"-named card (expected 0 per
   AFS Preconditions) to compare against after Cancel, per the shared-env
   guidance (don't hardcode an absolute against a shared, accumulating env).
2-3. Click "+ Toolkit"; verify the wizard opens (URL-based — the "Choose the
   toolkit type" heading carries no testid, and the URL check alone already
   satisfies the case's own step-3 observable per the AFS).
4-5. Search "art" in the type-picker; verify exactly one card (Artifact)
   remains, under STORAGE.
6-7. Click the Artifact card (via its testid, never text-matching — a
   text-based locator resolves to a non-interactive ancestor and silently
   no-ops); verify the "New Artifact Toolkit" form opens.
8-10. Fill Name="cancelled-toolkit" and Bucket="cancelled-bucket" (MUI fields
   — click()+press_sequentially(), never fill()); verify both Save and
   Cancel become active once the form is dirty.
11-12. Click Cancel -> confirm "Discard" in the Warning dialog (a two-click
   sequence the case's single "Click Cancel" step under-specifies); soft-
   assert the post-cancel URL returns to the Toolkits list (KNOWN DEFECT
   #655 — fails today, by design).
13. Search the Toolkits list for "cancelled-toolkit"; verify 0 matching
   cards (== the step-1 baseline) and the "No toolkits yet" empty state.
14-16. Navigate to Artifacts; open the bucket search; search "cancelled".
17-18. Verify 0 buckets named "cancelled-bucket" (== a baseline captured the
   same way at step 1) via both the UI (empty-state message) and the
   network log (no POST ever fired to the toolkit-create or bucket-create
   endpoint across the entire flow — the strongest proof Cancel aborts
   before any mutating call).

AFS: test-specs/artifacts/l3_cancel-artifact-toolkit-creation-no-toolkit-no-bucket_ELITEA-1868.md

Markers:
    - ui: requires browser
    - regression: regression test
    - toolkits: toolkit-creation-flow test
    - p2: medium priority (matches case priority — AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/toolkits/test_toolkit_creation_cancel_no_toolkit_no_bucket.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from pages.toolkit_creation_page import ToolkitCreationPage
from pages.toolkits_list_page import ToolkitsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.toolkits]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
DIALOG_TIMEOUT = 10_000

TOOLKIT_NAME = "cancelled-toolkit"
BUCKET_NAME = "cancelled-bucket"

# Filed separately as github.com/EliteaAI/elitea-testing-public#656 (MINOR,
# non-gating) — fires on every load of the type-picker screen, unrelated to
# this case's own pass/fail criteria. Exact filed signature only, so a
# genuinely new console error still fails this test.
KNOWN_NONGATING_CONSOLE_SIGNATURES = (
    'Each child in a list should have a unique "key" prop',
)


def _is_known_nongating_console_error(text: str) -> bool:
    return any(sig in text for sig in KNOWN_NONGATING_CONSOLE_SIGNATURES)


@allure.epic("Toolkits")
@allure.feature("Toolkit Creation Wizard — Cancel Flow")
class TestToolkitCreationCancelNoToolkitNoBucket:
    """ELITEA-1868 — Cancel during Artifact toolkit creation creates nothing.

    Read-only-by-default (workflow skill Hard Rule 10): the case's entire
    premise is that Cancel creates neither a toolkit nor a bucket, so there
    is no state for this test to seed or clean up — the observable is
    asserted directly against the live, shared project data (a
    baseline-captured count, never a hardcoded absolute).
    """

    @pytest.mark.p2
    @allure.title(
        "Cancel during Artifact toolkit creation creates no toolkit and no bucket"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1868_cancel-artifact-toolkit-creation-no-toolkit-no-bucket.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/655",
        "Known defect #655 — Cancel does not navigate back to the Toolkits list",
    )
    def test_cancel_artifact_toolkit_creation_creates_no_toolkit_no_bucket(self, page):
        """Cancel -> Discard on the Artifact toolkit form creates nothing.

        The one known-defect step (post-cancel navigation, #655) is
        ``expect.soft()``-asserted against the case's documented CORRECT
        expected value (the Toolkits list) — confirmed live to fail today —
        so the rest of the flow (steps 13-18) still runs and verifies the
        case's actual namesake objective.
        """
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg)
            if msg.type == "error" and not _is_known_nongating_console_error(msg.text)
            else None,
        )

        toolkits_list = ToolkitsListPage(page)
        toolkit_creation = ToolkitCreationPage(page)
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Precondition check — capture the pre-test baseline count for "
            f"'{BUCKET_NAME}' (AFS Preconditions: confirmed absent at start; "
            "compared against, not hardcoded, since a shared env accumulates "
            "other tests' data)"
        ):
            artifacts_page.navigate_to_artifacts()
            baseline_bucket_matches = artifacts_page.count_bucket_rows(BUCKET_NAME)
            assert baseline_bucket_matches == 0, (
                f"Precondition: no bucket named '{BUCKET_NAME}' should exist "
                f"before this test runs, found {baseline_bucket_matches}"
            )

        with allure.step("Step 1 — Navigate to the Toolkits section; verify the list is shown"):
            toolkits_list.navigate()
            assert toolkits_list.count_visible_cards() > 0, (
                "Toolkits list should show at least one existing toolkit card"
            )
            # Baseline (captured at test start, per AFS Preconditions the
            # project should have none matching this case's own literal
            # test-data name) — compared against, never hardcoded, since a
            # shared env accumulates other tests' data.
            toolkits_list.search(TOOLKIT_NAME)
            baseline_toolkit_matches = toolkits_list.count_visible_cards(timeout=3000)
            assert baseline_toolkit_matches == 0, (
                f"Precondition: no toolkit named '{TOOLKIT_NAME}' should exist "
                f"before this test runs, found {baseline_toolkit_matches}"
            )

        # Start capturing mutating requests now, so the window covers the
        # entire wizard flow that follows (AFS § Network Behavior / step 18).
        toolkit_create_requests = toolkits_list.capture_requests_matching(
            "elitea_core/tools", method="POST",
        )
        bucket_create_requests = toolkits_list.capture_requests_matching(
            "artifacts/buckets", method="POST",
        )

        with allure.step("Step 2 — Click the '+ Toolkit' button"):
            toolkits_list.click_create_toolkit(timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            "Step 3 — Verify the 'New Toolkit' wizard opens (URL-based check "
            "— the 'Choose the toolkit type' heading carries no testid, and "
            "the URL already satisfies this step's own observable per the AFS)"
        ):
            assert "/toolkits/create" in page.url, (
                f"Expected the wizard's type-picker URL, got: {page.url}"
            )

        with allure.step("Step 4 — Type 'art' in the type-picker search field"):
            toolkit_creation.search_toolkit_type("art")
            expect(toolkit_creation.type_search_input).to_have_value(
                "art", timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 5 — Verify only the 'Artifact' toolkit is displayed under 'STORAGE'"
        ):
            assert toolkit_creation.count_type_cards(timeout=UI_ELEMENT_TIMEOUT) == 1, (
                "Exactly one toolkit-type card should remain after filtering to 'art'"
            )
            artifact_card = toolkit_creation.get_type_card("artifact")
            expect(artifact_card).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 6 — Click the 'Artifact' toolkit card (via its testid, "
            "never text-matching — a text-based locator resolves to a "
            "non-interactive ancestor and silently no-ops)"
        ):
            artifact_card.click()
            assert "/toolkits/create/artifact" in page.url, (
                f"Expected navigation to the Artifact config form, got: {page.url}"
            )

        with allure.step(
            "Step 7 — Verify the 'New Artifact Toolkit' configuration form opens"
        ):
            expect(toolkit_creation.name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            bucket_field = toolkit_creation.get_field_locator("bucket")
            expect(bucket_field).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_creation.save_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f"Step 8 — Enter '{TOOLKIT_NAME}' into the Toolkit Name field"):
            toolkit_creation.fill_name(TOOLKIT_NAME)
            expect(toolkit_creation.name_input).to_have_value(
                TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(f"Step 9 — Enter '{BUCKET_NAME}' into the Bucket field"):
            toolkit_creation.fill_field("bucket", BUCKET_NAME)
            expect(bucket_field).to_have_value(BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 10 — Verify both Save and Cancel are visible and ACTIVE "
            "(Save is disabled until the form is dirty — steps 8/9 just did that)"
        ):
            assert toolkit_creation.is_save_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                "Save button should be enabled once the form is dirty"
            )
            assert toolkit_creation.is_cancel_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                "Cancel button should be visible and enabled"
            )

        with allure.step(
            "Step 11 — Click Cancel; confirm 'Discard' in the Warning dialog "
            "(two-click sequence — the case's single 'Click Cancel' step "
            "under-specifies the live product's confirmation dialog)"
        ):
            expect(toolkit_creation.cancel_confirm_dialog).not_to_be_visible()
            toolkit_creation.cancel_button.click()
            expect(toolkit_creation.cancel_confirm_dialog).to_be_visible(
                timeout=DIALOG_TIMEOUT,
            )
            expect(toolkit_creation.cancel_confirm_dialog).to_contain_text(
                "Are you sure you want to cancel creation of this toolkit?",
                timeout=UI_ELEMENT_TIMEOUT,
            )
            toolkit_creation.cancel_confirm_button.click()

        with allure.step(
            "Step 12 — Verify the form closes and the user is navigated back "
            "to the Toolkits list (KNOWN DEFECT #655: fails today — the app "
            "falls back to the type-picker at the same URL instead)"
        ):
            # Known defect: #655 — soft-assert the case's documented CORRECT
            # expected value (the Toolkits list URL). Confirmed live this
            # fails today: confirming Cancel leaves the URL at
            # /toolkits/create/artifact?viewMode=owner instead of navigating
            # anywhere. Soft so steps 13-18 (the case's actual namesake
            # objective — no toolkit/bucket created) still run — sanctioned-
            # RED exception per .agents/testing.md § Merge gate.
            expect.soft(
                page,
                "Known defect: #655 — confirming Cancel should navigate back "
                "to the Toolkits list",
            ).to_have_url(re.compile(r".*/toolkits/all(\?|$)"), timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 13 — Search the Toolkits list for '{TOOLKIT_NAME}'; verify "
            f"0 matches (== the baseline captured in Step 1) and the empty state"
        ):
            # Decouples this assertion from wherever step 12 actually landed
            # (KNOWN DEFECT #655) — navigate to the list directly.
            toolkits_list.navigate()
            toolkits_list.search(TOOLKIT_NAME)
            matches_after_cancel = toolkits_list.count_visible_cards(timeout=3000)
            assert matches_after_cancel == baseline_toolkit_matches, (
                f"No toolkit named '{TOOLKIT_NAME}' should exist after "
                f"cancelling creation — expected {baseline_toolkit_matches} "
                f"(the pre-test baseline), found {matches_after_cancel}"
            )
            expect(toolkits_list.empty_state_title).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step("Step 14 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step("Step 15 — Click the search icon in the 'BUCKETS' header"):
            artifacts_page.open_bucket_search(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 16 — Type 'cancelled' into the search field"):
            search_term = "cancelled"
            artifacts_page.search_buckets(search_term)
            expect(artifacts_page.bucket_search_input).to_have_value(
                search_term, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            f"Steps 17-18 — Verify no bucket named '{BUCKET_NAME}' appears in "
            f"the filtered results (DOM-count == 0), AND verify it was never "
            f"created at all — no POST ever fired to the toolkit-create or "
            f"bucket-create endpoint across the whole flow"
        ):
            bucket_matches = artifacts_page.count_bucket_rows(BUCKET_NAME)
            assert bucket_matches == baseline_bucket_matches, (
                f"No bucket named '{BUCKET_NAME}' should exist after "
                f"cancelling toolkit creation — expected {baseline_bucket_matches} "
                f"(the pre-test baseline), found {bucket_matches}"
            )
            assert not artifacts_page.bucket_exists(BUCKET_NAME, timeout=3000), (
                f"Bucket '{BUCKET_NAME}' should not appear in the filtered "
                f"bucket list"
            )

            assert not toolkit_create_requests, (
                f"Cancel should never trigger a POST to the toolkit-create "
                f"endpoint, but captured: {toolkit_create_requests}"
            )
            assert not bucket_create_requests, (
                f"Cancel should never trigger a POST to the bucket-create "
                f"endpoint, but captured: {bucket_create_requests}"
            )

        with allure.step(
            "Side-channel check — no NEW console errors across the full "
            "navigate -> type-picker -> fill-form -> cancel-confirm flow "
            "(the filed, non-gating #656 'unique key' warning is excluded "
            "by its exact signature, not a blanket suppression)"
        ):
            assert not console_errors, (
                "Unexpected console errors during the cancel flow: "
                f"{[m.text for m in console_errors]}"
            )
