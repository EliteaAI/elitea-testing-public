"""UI Test for ELITEA-1833 — Upload Flow, Duplicate Handling: Close X Button
on the Resolve Duplicates Modal.

Regression test: verifies that clicking the X (close) icon in the top-right
corner of the "Resolve duplicates" modal closes the modal WITHOUT uploading
anything and leaves the original file completely unchanged.

Test flow:
1. Seed a fresh bucket (via API) with ``sample.txt``.
2. Open the bucket; baseline the file count and the backend metadata.
3. Select a DIFFERENT-length ``sample.txt`` in the native file picker and
   confirm the "Upload files to ..." dialog.
4. Click "Upload" — client-side duplicate detection (confirmed live: zero
   network requests).
5. Click the dialog's X icon — confirmed live: zero network requests, the
   dialog closes, and the parent "Upload files to ..." dialog does NOT
   re-appear (the X dismisses the whole upload interaction rather than
   falling back a step).
6. No success toast; the original's count, ``lastModified``, ``size`` and
   bytes are all unchanged, re-verified after a page reload so the server
   — not a stale client listing — is the oracle.

Relationship to ELITEA-1832 (`test_artifacts_upload_duplicate_cancel.py`):
that spec clicks the dialog's **Cancel button** with a two-file (duplicate +
non-duplicate) batch. This one clicks the **X control** with a single file.
Honest note (AFS § Overlap check, source-verified): in the current build
``DuplicateResolutionDialog.jsx`` passes the same ``onCancel`` handler to
both ``Modal.BaseModal``'s ``onClose`` (which the X calls) and the Cancel
button's ``onClick``, so the two tests exercise one product path TODAY —
an implementation fact, not a coverage fact. The X is a real,
user-reachable affordance the case is written against, and the wiring can
change without either case changing.

Substitution declared (fidelity): the ONLY substitution is the API seed of
the precondition file (``artifact_api.upload_file``) — transit only, to
create the collision the case needs. Every asserted observable (dialog
state, request trace, toast absence, file count, metadata and bytes) is
produced by the product.

AFS: test-specs/artifacts/l3_upload-flow-duplicate-close-x-button_ELITEA-1833.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority; same marker ELITEA-1831/1832 use)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_duplicate_close_x.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
ABSENCE_CHECK_TIMEOUT = 3_000     # short polled wait for an element expected NOT to appear
TABLE_REFETCH_TIMEOUT = 15_000    # file table settle after navigation/reload
# Same rationale as ELITEA-1832 step 12: assert toast absence with Playwright's
# auto-retrying `expect` over a short POLLED window (never a raw sleep), so the
# assertion is robust whether no toast ever fires or one fires-and-dismisses.
TOAST_ABSENCE_POLL_TIMEOUT = 2_000

# The file table's "Last update" column clips below ~1600 px (test-specs/
# artifacts/_surface.md) — same viewport the sibling artifacts specs pin.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

DUPLICATE_FILE_NAME = "sample.txt"
# Deliberately DIFFERENT byte lengths (AFS § Test Data): if the X wrongly
# uploaded, BOTH size and content would change — which makes "unchanged" a
# strong claim rather than a coincidence of identical bytes.
ORIGINAL_CONTENT = b"ORIGINAL sample.txt content, seeded before the X-close attempt.\n"
REPLACEMENT_CONTENT = (
    b"NEVER-UPLOADED sample.txt content - the Resolve duplicates dialog is "
    b"dismissed via its X icon before any write can happen.\n"
)


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Duplicate Handling")
class TestArtifactUploadDuplicateCloseX:
    """ELITEA-1833 — the X icon closes 'Resolve duplicates' without uploading.

    Verifies the dialog closes, the parent upload dialog does not re-open,
    zero network requests fire, no toast appears, and the original file's
    count/timestamp/size/bytes survive a page reload untouched.
    """

    @pytest.mark.p2
    @allure.title(
        "X (close) icon on 'Resolve duplicates' closes the modal without "
        "uploading, leaving the original file unchanged"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1833_upload-flow-duplicate-close-x-button.md",
        "onetest-ai Test Case link",
    )
    def test_close_x_dismisses_duplicate_dialog_without_uploading(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """The X icon dismisses the duplicate dialog; nothing is uploaded.

        Substitution declared: the precondition file is seeded via the API
        (transit only — it merely creates the collision the case needs);
        every asserted observable is produced by the product.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Setup (preconditions, not case steps) — seed sample.txt into the
        # fresh bucket via the API, and write the same-named,
        # different-length local file into tmp_path (project convention;
        # no checked-in upload-fixture directory exists).
        # ------------------------------------------------------------------
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifact_api.upload_file(
            bucket_name, DUPLICATE_FILE_NAME, ORIGINAL_CONTENT, content_type="text/plain",
        )
        baseline_metadata = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
        assert baseline_metadata is not None, (
            f"Seed file '{DUPLICATE_FILE_NAME}' should exist in bucket "
            f"'{bucket_name}' immediately after seeding via the API"
        )

        upload_file_path = tmp_path / DUPLICATE_FILE_NAME
        upload_file_path.write_bytes(REPLACEMENT_CONTENT)
        assert len(REPLACEMENT_CONTENT) != len(ORIGINAL_CONTENT), (
            "Test-data invariant: the selected file must differ in byte "
            "length from the seed, so an accidental upload could not hide "
            "behind identical metadata"
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step(
            "Step 2 — Select the bucket that already contains sample.txt"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: '{DUPLICATE_FILE_NAME}' should be visible in "
                f"bucket '{bucket_name}' after seeding"
            )
            artifacts_page.wait_for_file_count(1, timeout=TABLE_REFETCH_TIMEOUT)
            baseline_count = artifacts_page.get_total_file_count_from_pagination()
            assert baseline_count == 1, (
                f"Expected exactly 1 file in the freshly seeded bucket before "
                f"the upload attempt, got {baseline_count}"
            )

        with allure.step(
            "Steps 3-5 — Click the upload icon (native file explorer opens "
            "immediately), select sample.txt, confirm; the 'Upload files "
            "to ...' modal opens"
        ):
            # Steps 3/4/5 are one mechanically inseparable Playwright action:
            # `expect_file_chooser` must wrap the click, and files are set the
            # instant the chooser resolves — there is no intermediate
            # observable between "click" and "files chosen" (the same folding
            # the AFS applies). If the chooser never opened, `upload_files()`
            # would raise a timeout here.
            artifacts_page.upload_files([str(upload_file_path)])

        with allure.step(
            "Step 6 — Verify the 'Upload files to ...' modal is open with the "
            "bucket-name Path prefix, then click Upload"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_prefix = artifacts_page.get_upload_path_normalized_prefix()
            assert path_prefix == f"{bucket_name}/", (
                f"Path field's read-only prefix should be exactly "
                f"'{bucket_name}/', got: {path_prefix!r}"
            )
            requests_during_detection = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_upload_path_upload_button()

        with allure.step(
            "Step 7 — Verify the 'Resolve duplicates' modal opens listing "
            "sample.txt, and that detection was purely client-side "
            "(zero network requests)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog(timeout=DIALOG_TIMEOUT)
            assert not requests_during_detection, (
                "Duplicate detection must be a purely client-side diff "
                "against the already-fetched bucket listing — no network "
                f"request should fire, but observed: {requests_during_detection}"
            )
            duplicate_names = artifacts_page.get_resolve_duplicates_filenames()
            assert duplicate_names == [DUPLICATE_FILE_NAME], (
                f"'Resolve duplicates' modal should list exactly "
                f"[{DUPLICATE_FILE_NAME!r}] as the duplicate, got: {duplicate_names}"
            )

        with allure.step(
            "Step 8 — Click the X (close) icon in the top-right corner of "
            "the 'Resolve duplicates' modal"
        ):
            requests_during_close = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_resolve_duplicates_close_button()

        with allure.step(
            "Step 9 — Verify the modal is closed, and that the parent "
            "'Upload files to ...' dialog does NOT re-appear (the X "
            "dismisses the whole upload interaction rather than falling "
            "back one step)"
        ):
            artifacts_page.wait_for_resolve_duplicates_dialog_closed(timeout=DIALOG_TIMEOUT)
            expect(artifacts_page.upload_path_dialog).to_have_count(
                0, timeout=ABSENCE_CHECK_TIMEOUT,
            )

        with allure.step(
            "Step 10 — Verify no file was uploaded (zero network requests "
            "from the X click onward — positive proof, not mere absence "
            "from the table) and no success notification is displayed"
        ):
            expect(artifacts_page.success_toast_message).to_have_count(
                0, timeout=TOAST_ABSENCE_POLL_TIMEOUT,
            )
            assert not requests_during_close, (
                "Closing the 'Resolve duplicates' dialog via its X icon must "
                "fire zero network requests — no upload, no rollback — but "
                f"observed: {requests_during_close}"
            )

        with allure.step(
            "Step 11 — Verify the original sample.txt is unchanged: file "
            "count, lastModified, size and bytes — re-verified after a page "
            "reload so the SERVER, not a stale client listing, is the oracle"
        ):
            page.reload()
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(1, timeout=TABLE_REFETCH_TIMEOUT)
            assert artifacts_page.get_total_file_count_from_pagination() == baseline_count, (
                f"Bucket file count should still be {baseline_count} after "
                f"closing the duplicate dialog via X"
            )
            assert artifacts_page.file_exists(DUPLICATE_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{DUPLICATE_FILE_NAME}' should still be listed after the reload"
            )

            metadata_after = artifact_api.get_file_metadata(bucket_name, DUPLICATE_FILE_NAME)
            assert metadata_after is not None, (
                f"'{DUPLICATE_FILE_NAME}' should still exist after the X close"
            )
            assert metadata_after["lastModified"] == baseline_metadata["lastModified"], (
                f"'{DUPLICATE_FILE_NAME}' lastModified must be unchanged: "
                f"before={baseline_metadata['lastModified']!r}, "
                f"after={metadata_after['lastModified']!r}"
            )
            assert metadata_after.get("size") == baseline_metadata.get("size"), (
                f"'{DUPLICATE_FILE_NAME}' size must be unchanged: "
                f"before={baseline_metadata.get('size')}, "
                f"after={metadata_after.get('size')}"
            )
            content_after = artifact_api.get_file(bucket_name, DUPLICATE_FILE_NAME)
            assert content_after == ORIGINAL_CONTENT, (
                f"'{DUPLICATE_FILE_NAME}' bytes must still be the ORIGINAL "
                "seed's, not the file selected in the aborted upload"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate → upload → duplicate → X-close flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the duplicate-close-X "
                f"upload flow: {[m.text for m in console_errors]}"
            )
