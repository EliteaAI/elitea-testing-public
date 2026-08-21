"""UI Test for ELITEA-1825 — Upload Flow: Cancel on the "Upload files to ..."
modal discards the file selection.

Regression test: verifies that clicking **Cancel** on the FIRST upload modal
— the one that opens the moment files are chosen in the native picker, before
"Upload" is ever pressed — closes the modal, uploads nothing, shows no success
notification, and leaves the bucket's file table byte-identical to its
baseline.

Not the same case as ELITEA-1832
(``test_artifacts_upload_duplicate_cancel.py``): that one cancels the
*second*, "Resolve duplicates" dialog, reachable only AFTER clicking Upload
(``DuplicateResolutionDialog.jsx``). This one cancels
``UploadPathDialog.jsx``'s own Cancel button, whose ``handleCancel`` resets
the dialog's folder-path state and closes it without ever reaching the
duplicate diff. Similar terminal observables (no toast, file absent, count
unchanged) because both abort an upload — different trigger, different
component, different product code path.

Test flow:
1. Seed a fresh bucket (via API) holding exactly one file, ``seed.txt`` — so
   "the file table is unchanged" is a real observable rather than
   empty-stays-empty.
2. Open the bucket in the UI and record the baseline (file names +
   pagination counter), read from the product's own rendered table.
3. Select ``sample1.txt`` in the native file picker; the "Upload files to ..."
   dialog opens with the Path prefix pre-filled with the bucket name and an
   empty editable segment.
4. Type ``probe-folder`` into the editable Path segment — makes the discard
   observable (Axis-2 A2-3).
5. Click **Cancel**: the dialog closes having fired ZERO ``artifacts``
   network requests (the strong form of "nothing was uploaded" — an absent
   table row alone could also be a stale listing).
6. No success toast; the file table equals its baseline in the client AND
   after a full page reload (the server as oracle).
7. Re-opening the upload dialog shows a CLEARED Path field — the discard is
   real state reset, not a hidden modal with stale pending state.

Fidelity: the bucket and its pre-existing ``seed.txt`` are created through
``ArtifactAPI`` (``artifact_bucket`` fixture + ``upload_file``) — **transit
substitution only**, declared in the AFS § Fidelity Declaration. The case's
preconditions state the bucket and its contents already exist; creation is
not a case step. Every asserted observable (the modal's behaviour, the zero
requests, the toast absence, the file table, the re-opened dialog's state) is
produced by the live product through the real UI upload flow. No response is
fabricated, no state injected.

AFS: test-specs/artifacts/l2_upload-flow-cancel-upload-modal-discards-file-selection_ELITEA-1825.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs
    - p2: medium priority (matches case priority)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_path_cancel.py -v
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
ABSENCE_CHECK_TIMEOUT = 3_000     # short wait for an element expected NOT to appear
# Same rationale as ELITEA-1832 step 12: assert toast absence with Playwright's
# auto-retrying `expect` over a short POLLED window (never a raw sleep), so the
# assertion is robust whether no toast ever fires or one fires-and-dismisses.
TOAST_ABSENCE_POLL_TIMEOUT = 2_000

# The file table's "Last update" column clips below ~1600 px (test-specs/
# artifacts/_surface.md) — same viewport the sibling artifacts specs pin.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

SEED_FILE_NAME = "seed.txt"
SEED_FILE_CONTENT = b"Pre-existing file, seeded before the cancelled upload attempt."
# The case's own literal file name (Test Data + step 5). Case step 10 writes
# "sample.txt" — an internal typo in the case text, resolved in the AFS
# § Findings: the assertion targets the file actually selected in step 5.
SELECTED_FILE_NAME = "sample1.txt"
SELECTED_FILE_CONTENT = b"never uploaded - cancelled\n"

# Typed into the editable Path segment before Cancel, so the discard has
# something to discard (AFS Axis-2 A2-3).
PROBE_FOLDER_PATH = "probe-folder"

# Live wording of the dialog's description line at bucket root (no subfolder
# prefix active) — UploadPathDialog.jsx's descriptionMessage useMemo.
UPLOAD_DIALOG_DESCRIPTION = (
    "Files will be uploaded to the selected bucket. Optionally, enter a folder "
    'path to organize your files. Use "/" to create nested folder(s).'
)


@allure.epic("Artifacts")
@allure.feature("Upload flow")
@allure.story("Cancel on the upload-path modal discards the file selection")
class TestArtifactsUploadPathCancel:
    """ELITEA-1825 — Cancel on the "Upload files to ..." modal uploads nothing.

    Read-only from the bucket's perspective at the end: the bucket is
    deliberately mutated exactly once (seeded with seed.txt) so that "the
    file table is unchanged" is observable at all — the minimal state the
    observable inherently requires (workflow skill Hard Rule 10) — and the
    test then proves that seeding mutation is the ONLY one that ever lands.
    """

    @pytest.mark.p2
    @allure.title(
        "Cancel on the 'Upload files to ...' modal closes it, uploads nothing, "
        "and leaves the file table unchanged"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1825_upload-flow-cancel-upload-modal-discards-file-selection.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_upload_modal_discards_file_selection(
        self, page, artifact_api, artifact_bucket, tmp_path,
    ):
        """Cancel on the upload-path modal discards the pending file selection."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Setup (preconditions, not case steps) — seed one pre-existing file
        # via the API, and write the file to be selected into tmp_path
        # (project convention; no checked-in fixture-files directory exists).
        # ------------------------------------------------------------------
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifact_api.upload_file(
            bucket_name, SEED_FILE_NAME, SEED_FILE_CONTENT, content_type="text/plain",
        )
        selected_file_path = tmp_path / SELECTED_FILE_NAME
        selected_file_path.write_bytes(SELECTED_FILE_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section in the left sidebar"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            expect(artifacts_page.buckets_heading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Select the bucket in the bucket list"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            expect(page).to_have_url(re.compile(rf"bucket={re.escape(bucket_name)}"))
            baseline_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            baseline_pagination = artifacts_page.get_pagination_info_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert baseline_names == [SEED_FILE_NAME], (
                f"Precondition: the freshly seeded bucket '{bucket_name}' should "
                f"list exactly ['{SEED_FILE_NAME}'], got {baseline_names}"
            )
            logger.info(
                "Baseline for %s: names=%s pagination=%r",
                bucket_name, baseline_names, baseline_pagination,
            )

        with allure.step(
            "Steps 3-6 — Click the upload icon (the native file explorer opens "
            f"immediately), select {SELECTED_FILE_NAME}, confirm"
        ):
            # Steps 3/4/5/6 are one mechanically inseparable Playwright action:
            # `expect_file_chooser` must wrap the click, and the files are set
            # the instant the chooser resolves — there is no intermediate
            # observable between "click" and "files chosen" (same folding the
            # AFS applies, and the same ELITEA-1832 uses). A chooser that never
            # opened raises a timeout here, which IS the assertion for steps 3-5.
            artifacts_page.upload_files([str(selected_file_path)])

        with allure.step(
            "Step 7 — Verify the 'Upload files to ...' modal opens with the "
            "Path field pre-filled with the bucket name"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            prefix = artifacts_page.get_upload_path_normalized_prefix()
            assert prefix == f"{bucket_name}/", (
                f"Path field's read-only prefix should be pre-filled with "
                f"'{bucket_name}/', got {prefix!r}"
            )
            typed_on_open = artifacts_page.get_upload_path_typed_value()
            assert typed_on_open == "", (
                f"The editable Path segment should be empty when the dialog "
                f"opens at bucket root, got {typed_on_open!r}"
            )
            assert (
                artifacts_page.get_upload_path_description_text(timeout=UI_ELEMENT_TIMEOUT)
                == UPLOAD_DIALOG_DESCRIPTION
            ), "Upload dialog description line should show the bucket-root wording"

        with allure.step(
            f"Axis-2 probe (before step 8) — type '{PROBE_FOLDER_PATH}' into the "
            "editable Path segment so the Cancel discard has state to discard"
        ):
            artifacts_page.fill_upload_path(PROBE_FOLDER_PATH)
            assert artifacts_page.get_upload_path_typed_value() == PROBE_FOLDER_PATH, (
                f"The editable Path segment should hold {PROBE_FOLDER_PATH!r} "
                "before Cancel is clicked"
            )

        with allure.step("Step 8 — Click 'Cancel' in the modal"):
            requests_during_cancel = artifacts_page.capture_requests_matching("artifacts")
            artifacts_page.click_upload_path_cancel_button()

        try:
            with allure.step(
                "Step 9 — Verify the modal is closed, and that Cancel fired ZERO "
                "network requests (proof nothing was uploaded, as opposed to "
                "uploaded-then-hidden)"
            ):
                artifacts_page.wait_for_upload_path_dialog_closed(timeout=DIALOG_TIMEOUT)
                assert not requests_during_cancel, (
                    "Cancel must discard the selection without any upload traffic — "
                    f"expected zero 'artifacts' requests, observed: "
                    f"{list(requests_during_cancel)}"
                )
        finally:
            requests_during_cancel.stop()

        # Checked BEFORE the reload below: a page reload would erase a toast
        # that did fire, destroying the evidence this assertion exists to find.
        with allure.step("Step 11 — Verify no success notification is displayed"):
            expect(artifacts_page.success_toast_message).to_have_count(
                0, timeout=TOAST_ABSENCE_POLL_TIMEOUT,
            )

        with allure.step(
            f"Step 10 — Verify '{SELECTED_FILE_NAME}' is NOT listed in the file "
            "table and the table is otherwise unchanged"
        ):
            assert not artifacts_page.file_exists(
                SELECTED_FILE_NAME, timeout=ABSENCE_CHECK_TIMEOUT
            ), (
                f"'{SELECTED_FILE_NAME}' must NOT appear in bucket "
                f"'{bucket_name}' — the upload was cancelled before it started"
            )
            assert artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT) == baseline_names, (
                "The bucket's file list must be identical to its baseline after Cancel"
            )
            assert (
                artifacts_page.get_pagination_info_text(timeout=UI_ELEMENT_TIMEOUT)
                == baseline_pagination
            ), (
                f"The pagination counter must still read {baseline_pagination!r} "
                "after Cancel"
            )

        with allure.step(
            "Step 10 (re-verified after a reload) — the SERVER, not the "
            "un-refreshed client listing, is the oracle for 'not uploaded'"
        ):
            page.reload()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT) == baseline_names, (
                "After a full reload the bucket must still list exactly its "
                f"baseline {baseline_names} — nothing reached the server"
            )

        with allure.step(
            "Axis-2 A2-3 — re-opening the upload dialog shows a CLEARED Path "
            "field (the discard is real state reset, not just a hidden modal)"
        ):
            artifacts_page.upload_files([str(selected_file_path)])
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            reopened_typed = artifacts_page.get_upload_path_typed_value()
            assert reopened_typed == "", (
                f"The re-opened dialog's editable Path segment must be empty — "
                f"{PROBE_FOLDER_PATH!r} was discarded by Cancel, got {reopened_typed!r}"
            )
            assert artifacts_page.get_upload_path_normalized_prefix() == f"{bucket_name}/", (
                "The re-opened dialog's read-only prefix should be the bucket root again"
            )
            # Leave no dialog open behind this test.
            artifacts_page.click_upload_path_cancel_button()
            artifacts_page.wait_for_upload_path_dialog_closed(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Side-channel check — no console errors across the "
            "navigate -> select -> cancel -> reload flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the cancelled upload flow: "
                f"{[m.text for m in console_errors]}"
            )
