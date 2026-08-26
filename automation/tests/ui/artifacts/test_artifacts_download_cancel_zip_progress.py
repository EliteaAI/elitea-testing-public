"""UI Test for ELITEA-1842 / ELITEA-1843 — Download Flow: cancelling an
in-progress ZIP preparation from the progress modal.

Family spec (ONE parameterized test, one row per TMS case) — the two cases
are flow-variants of a single flow, differing only in WHICH control aborts
the in-flight ZIP preparation:

* **ELITEA-1842** — the modal's "Cancel" button, with 4 files selected.
* **ELITEA-1843** — the modal's X (close) icon, with 3 files selected.

Source-confirmed (``ZipDownloadProgressDialog.jsx``): one ``onCancel``
handler is passed to BOTH ``BaseModal``'s ``onClose`` (X / backdrop /
Escape) and the Cancel button's ``onClick`` — the same shape
``DuplicateResolutionDialog`` uses (ELITEA-1832 / ELITEA-1833).

Each row asserts its OWN expected values (selection size, counter text,
``aria-valuenow``); ELITEA-1842's steps 10-11 (file table intact, selection
retained) are asserted for both rows — for ELITEA-1843 that is a declared
Axis-2 addition, not case coverage (AFS § Coverage Map).

Test flow (mirrors the AFS's own Test Steps 1-8):
1. Seed a fresh bucket (via API) with the case's 4 files under ``a1/`` and
   navigate straight into that subfolder (folds AFS steps 1-2, same folding
   precedent as ELITEA-1840/1841).
2. Select the row's file count via per-row checkboxes; verify exactly those
   read checked and the toolbar "Download files" button enables.
3. Click "Download files"; verify the ZIP-preparation dialog opens with the
   right title, a determinate progress bar, the counter, and BOTH abort
   controls present (Cancel button + X close button).
4. Poll until the counter reports ``1 of N files`` — proof the download is
   genuinely in progress — verify the matching ``aria-valuenow`` and the
   current-file label, then click the row's abort control.
5. Verify the dialog closes and a toast reading exactly "Download cancelled"
   appears.
6. Verify NO ZIP was ever handed to the browser (no download event fired at
   any point in the test).
7. Verify the file table still lists all 4 seeded files and the selected
   checkboxes are still checked.
8. Verify no console errors occurred across the whole flow.

**Timing control, not substitution** (``.agents/testing.md`` § Fidelity
policy): with small files the whole ZIP flow finishes in under two seconds,
too fast for "while the download is in progress" to be a real state. This
test delays the product's OWN per-file artifact GETs via ``page.route()`` +
``route.continue_()`` — every byte still comes from the DEV backend, nothing
is fabricated. Same technique
``test_artifacts_download_all_files_select_all_zip.py`` (ELITEA-1841) ships.

AFS: test-specs/artifacts/l3_download-flow-cancel-zip-progress-modal_ELITEA-1842-1843.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches both cases' priority — AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_download_cancel_zip_progress.py -v
"""

import logging
import time

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms unless noted)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, checkboxes, dialog elements
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
# The toast fires only once the ABORTED in-flight fetch rejects, i.e. after
# the dialog has already unmounted — give it room (live: ~2s under the
# route delay).
TOAST_TIMEOUT = 15_000
# Ceiling for the "counter reached 1 of N" poll — comfortably above one
# route-delayed file transfer.
PROGRESS_WAIT_TIMEOUT = 30_000

FOLDER_NAME = "a1"
FILE_QA = "Q&A.docx.odt"
FILE_REGRESSION = "Regression test cases.odt"
FILE_SHAREPOINT = "sharepoint.docx"
FILE_GIF = "sample_640x426.gif"

# The source cases' own file set (both list bucket-1/a1's files).
SEEDED_FILES = {
    FILE_QA: (
        b"Q&A docx odt content for ELITEA-1842/1843 cancel-download test\n" * 40,
        "application/vnd.oasis.opendocument.text",
    ),
    FILE_REGRESSION: (
        b"Regression test cases odt content for ELITEA-1842/1843\n" * 40,
        "application/vnd.oasis.opendocument.text",
    ),
    FILE_SHAREPOINT: (
        b"sharepoint docx content for ELITEA-1842/1843\n" * 40,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    FILE_GIF: (
        b"GIF89a" + b"FAKE_GIF_BYTES_FOR_ELITEA_1842_1843" * 40,
        "image/gif",
    ),
}

ALL_SEEDED_NAMES = set(SEEDED_FILES.keys())

# Per-request delay (seconds) applied ONLY to this test's own page, on the
# product's own artifact-download GETs. Timing control (a REAL response,
# delayed), never a fabricated one — see the module docstring.
ROUTE_DELAY_SECONDS = 1.2

# How long to keep watching for a ZIP download after the cancel before
# declaring "no ZIP was saved". Must exceed the remaining route-delay budget
# for the un-fetched files so a wrongly-continuing download would be caught.
NO_DOWNLOAD_OBSERVATION_SECONDS = 6.0

CANCEL_TOAST_TEXT = "Download cancelled"

TRIGGER_CANCEL_BUTTON = "cancel_button"
TRIGGER_CLOSE_X = "close_x"


def _delayed_route(route):
    """Delay the product's own artifact GET, then let it through untouched.

    Guarded: once the download is cancelled the request is aborted, and
    ``continue_()`` on an already-dead request raises — harmless here, and
    swallowing it keeps a cancelled route from polluting the run.
    """
    time.sleep(ROUTE_DELAY_SECONDS)
    try:
        route.continue_()
    except Exception as exc:  # request aborted by the cancel under test
        logger.debug("Route continue skipped (request already aborted): %s", exc)


@allure.epic("Artifacts")
@allure.feature("Download Flow")
class TestArtifactDownloadCancelZipProgress:
    """ELITEA-1842 / ELITEA-1843 — aborting an in-progress ZIP preparation
    from the progress modal, via the Cancel button and via the X close icon.

    Verifies that the abort closes the modal, raises the "Download cancelled"
    notification, saves NO ZIP, and leaves the file table and its selection
    untouched.
    """

    @pytest.mark.p2
    @pytest.mark.parametrize(
        ("case_id", "files_selected", "trigger", "expected_counter", "expected_valuenow"),
        [
            pytest.param(
                "ELITEA-1842", 4, TRIGGER_CANCEL_BUTTON, "1 of 4 files", "25",
                id="ELITEA-1842-cancel-button",
            ),
            pytest.param(
                "ELITEA-1843", 3, TRIGGER_CLOSE_X, "1 of 3 files", "33",
                id="ELITEA-1843-close-x-button",
            ),
        ],
    )
    @allure.title(
        "Aborting an in-progress ZIP preparation from the progress modal "
        "stops the download, notifies, and leaves the table untouched"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/tree/main/tests/"
        "automated-full-regression-ui/artifacts",
        "onetest-ai Test Case link (ELITEA-1842 / ELITEA-1843)",
    )
    def test_cancel_in_progress_zip_download(
        self, page, artifact_api, artifact_bucket,
        case_id, files_selected, trigger, expected_counter, expected_valuenow,
    ):
        """Cancelling mid-flight aborts the ZIP preparation.

        Substitutions declared (AFS § Fidelity Declaration): (1) the bucket
        and its files are seeded through ``ArtifactAPI`` rather than the UI
        upload dialog — both cases carry them as a PRECONDITION, not a step,
        and every asserted observable is still produced by the product
        (transit only); (2) ``page.route()`` delays the product's own
        artifact GETs so "while the download is in progress" is a real,
        observable state — timing control, not a fabricated response.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # Registered BEFORE anything can download — an empty list at the end
        # is the evidence for case step 9 ("no ZIP file is saved"). An
        # expect_download() context could only ever prove the opposite.
        downloads = []
        page.on("download", lambda d: downloads.append(d.suggested_filename))

        # Delay ONLY the single-file artifact-download GETs, scoped to this
        # test's own page instance.
        page.route("**/artifact/default/**", _delayed_route)

        # ------------------------------------------------------------------
        # Precondition — seed the case's 4 files under a1/ into the fresh
        # bucket via API (ArtifactAPI.upload_file auto-creates the folder
        # node; established precedent of every merged download spec).
        # ------------------------------------------------------------------
        for filename, (content, content_type) in SEEDED_FILES.items():
            artifact_api.upload_file(
                bucket_name, f"{FOLDER_NAME}/{filename}", content,
                content_type=content_type,
            )

        artifacts_page = ArtifactsPage(page)
        files_to_select = sorted(ALL_SEEDED_NAMES)[:files_selected]

        with allure.step(
            f"Step 1 [{case_id}] — Navigate directly to the bucket's "
            f"'{FOLDER_NAME}' subfolder (folds AFS Test Steps 1-2) and verify "
            "the 4 seeded files are listed with the toolbar download button "
            "initially disabled"
        ):
            artifacts_page.navigate_to_bucket_folder(
                bucket_name, FOLDER_NAME, timeout=NAVIGATION_TIMEOUT,
            )
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert set(file_names) == ALL_SEEDED_NAMES, (
                f"Expected exactly the 4 seeded files, got {file_names}"
            )
            expect(artifacts_page.download_files_button).to_be_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f"Step 2 [{case_id}] — Select {files_selected} file(s) via their "
            "row checkboxes; verify exactly those read checked and the "
            "toolbar 'Download files' button becomes enabled"
        ):
            for filename in files_to_select:
                artifacts_page.select_file_checkbox(filename, timeout=UI_ELEMENT_TIMEOUT)

            checkbox_states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert {n for n, checked in checkbox_states.items() if checked} == set(
                files_to_select
            ), (
                f"Expected exactly {files_to_select} checked, got: {checkbox_states}"
            )
            expect(artifacts_page.download_files_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f"Step 3 [{case_id}] — Click 'Download files'; verify the "
            "ZIP-preparation dialog opens with the correct title, a "
            "determinate progress bar, the file counter, and BOTH abort "
            "controls (Cancel button and X close icon)"
        ):
            artifacts_page.download_files_button.click()

            expect(artifacts_page.zip_download_progress_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.zip_download_progress_title).to_have_text(
                f"Preparing {bucket_name}.zip", timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.zip_download_progress_bar).to_have_attribute(
                "aria-valuemin", "0"
            )
            expect(artifacts_page.zip_download_progress_bar).to_have_attribute(
                "aria-valuemax", "100"
            )
            expect(artifacts_page.zip_download_progress_counter).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.zip_download_progress_cancel_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.zip_download_progress_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f"Step 4 [{case_id}] — Wait until the counter reports "
            f"'{expected_counter}' (proof the download is genuinely in "
            f"progress), verify aria-valuenow='{expected_valuenow}' and the "
            f"current-file label, then abort via the '{trigger}' control"
        ):
            frame = artifacts_page.wait_for_zip_progress_at_least(
                1, timeout=PROGRESS_WAIT_TIMEOUT
            )
            assert frame["total"] == files_selected, (
                f"Expected the counter's total to be {files_selected} "
                f"(the selected file count), got: {frame}"
            )
            assert f"{frame['current']} of {frame['total']} files" == expected_counter, (
                f"Expected the abort to land at '{expected_counter}', got: {frame}"
            )
            assert frame["valuenow"] == expected_valuenow, (
                f"Expected aria-valuenow='{expected_valuenow}' at "
                f"'{expected_counter}', got {frame['valuenow']!r}"
            )
            assert frame["current_file"].startswith(f"Current: {FOLDER_NAME}/"), (
                "Current-file label should show the full relative key of the "
                f"file in flight, got: {frame['current_file']!r}"
            )

            if trigger == TRIGGER_CANCEL_BUTTON:
                artifacts_page.click_zip_download_cancel_button(timeout=UI_ELEMENT_TIMEOUT)
            else:
                artifacts_page.click_zip_download_close_button(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 5 [{case_id}] — Verify the progress modal closes and a "
            f"'{CANCEL_TOAST_TEXT}' notification is displayed"
        ):
            expect(artifacts_page.zip_download_progress_dialog).to_be_hidden(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # The toast is raised by the ABORTED fetch's rejection, i.e.
            # strictly after the dialog has unmounted — asserted separately,
            # with its own generous timeout.
            expect(artifacts_page.success_toast_message).to_have_text(
                CANCEL_TOAST_TEXT, timeout=TOAST_TIMEOUT
            )

        with allure.step(
            f"Step 6 [{case_id}] — Verify no ZIP file was saved: no download "
            "event fired at any point, including a full observation window "
            "after the cancel"
        ):
            # Not a synchronization sleep (Hard Rule 5): proving the ABSENCE
            # of an event has no condition to wait on — this is the
            # observation window, sized to outlast the remaining
            # route-delay budget of the files that were never fetched.
            time.sleep(NO_DOWNLOAD_OBSERVATION_SECONDS)
            assert downloads == [], (
                "Cancelling the ZIP preparation must abort the download — but "
                f"the browser was handed: {downloads}"
            )

        with allure.step(
            f"Step 7 [{case_id}] — Verify the file table remains intact (all "
            "4 seeded files still listed) and the selected checkboxes are "
            "still checked after cancellation"
        ):
            post_cancel_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert set(post_cancel_names) == ALL_SEEDED_NAMES, (
                "The file table should be unchanged by a cancelled download, "
                f"got {post_cancel_names}"
            )
            post_cancel_states = artifacts_page.get_checkbox_states(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert {n for n, checked in post_cancel_states.items() if checked} == set(
                files_to_select
            ), (
                "Previously selected files should remain checked after "
                f"cancellation, got: {post_cancel_states}"
            )

        with allure.step(
            f"Pass criterion [{case_id}] — no console errors occurred across "
            "the whole select + download + cancel flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the cancel-download flow: "
                f"{[m.text for m in console_errors]}"
            )
