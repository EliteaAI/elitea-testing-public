"""UI Test for ELITEA-1841 — Download Flow: Download All Files Using the
Table-Header "Select All" Checkbox as ZIP.

Regression test: verifies that clicking the table-header "Select all"
checkbox in an artifacts subfolder (6 seeded files) checks all 6 rows AND
lands the header checkbox itself in a fully-checked/non-indeterminate state,
that the toolbar "Download files" button enables with an invariant tooltip,
that clicking it opens the ZIP-preparation progress dialog and the
counter/progress-bar/current-file trio progress through the FULL "1 of 6" ->
"6 of 6" range (not just a single frame), that the ZIP downloads as
"{bucket}.zip" containing exactly the 6 seeded files flattened to root and
byte-identical to what was seeded, and that ``zipfile.testzip()`` returns
``None`` (CRC-clean).

Test flow (mirrors the AFS's own Test Steps 1-10, with steps 1-2 folded per
the AFS's own instruction, same folding precedent ELITEA-1840 already used):
1. Seed a fresh bucket (via API) with 6 files under ``a1/`` (the case's own
   file set) and navigate directly to that subfolder in one URL navigation.
2. Click the table-header "Select all" checkbox; verify all 6 rows become
   checked AND the header checkbox itself lands fully-checked/non-
   indeterminate (a different code path/element from ELITEA-1840's per-row
   checkbox clicks).
3. Verify the toolbar "Download files" button transitions from disabled to
   enabled, with a tooltip text that is INVARIANT across partial/full
   selection (contrast with the delete button's tooltip, which does vary).
4. Click "Download files"; verify the ZIP-preparation dialog shows the
   correct title, a determinate progress bar, a file counter, a current-file
   label, and a Cancel button.
5. Poll the counter/progress-bar/current-file trio while the dialog is
   visible (via a ``page.route()`` network delay scoped to this test only)
   and assert the FULL monotonic progression 1-of-6 through 6-of-6 — the
   differentiator from ELITEA-1840's single-frame spot-check (justified
   there only because 2 files barely exhibits "progression").
6. Verify the dialog auto-closes and a ZIP file named exactly
   ``{bucket_name}.zip`` downloads.
7. Verify the ZIP's namelist is exactly the 6 seeded file names, flattened to
   the ZIP root (not nested under ``a1/``).
8. Verify each of the 6 entries is byte-identical to the seeded content, and
   ``zipfile.ZipFile.testzip()`` returns ``None`` (CRC-clean) — a stronger,
   purpose-built "not corrupted" signal new to this case.
9. Verify no console errors occurred across the whole flow.

Fresh sibling spec, NOT an extension of
``test_artifacts_download_multiple_files_zip.py`` — see the AFS's own
"Coverage Map vs ELITEA-1840" section for the full reasoning (a categorically
different selection mechanism, a brand-new header-checkbox element with its
own testid gap, and a materially stronger progress-sequence assertion).

AFS: test-specs/artifacts/l2_download-flow-all-files-select-all-checkbox-zip_ELITEA-1841.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_download_all_files_select_all_zip.py -v
"""

import logging
import re
import time
import zipfile

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms unless noted)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, checkboxes, dialog elements
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
# Generous — must accommodate the artificial per-request route delay below
# applied to all 6 sequential GETs, plus JSZip generation and the blob-URL
# download.
DOWNLOAD_TIMEOUT = 30_000
# Safety ceiling for the progress-frame polling loop — well above the
# expected ~3.6s (6 files x 0.6s route delay) plus overhead.
MAX_POLL_DURATION_MS = 15_000

FOLDER_NAME = "a1"
FILE_QA = "Q&A.docx.odt"
FILE_REGRESSION = "Regression test cases.odt"
FILE_SHAREPOINT = "sharepoint.docx"
FILE_GIF = "sample_640x426.gif"
FILE_PNG = "sample.png"
FILE_TXT = "sample.txt"

SEEDED_FILES = {
    FILE_QA: (
        b"Q&A docx odt content for ELITEA-1841 select-all ZIP test\n",
        "application/vnd.oasis.opendocument.text",
    ),
    FILE_REGRESSION: (
        b"Regression test cases odt content for ELITEA-1841\n",
        "application/vnd.oasis.opendocument.text",
    ),
    FILE_SHAREPOINT: (
        b"sharepoint docx content for ELITEA-1841\n",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    FILE_GIF: (
        b"GIF89a" + b"FAKE_GIF_BYTES_FOR_ELITEA_1841_TEST",
        "image/gif",
    ),
    FILE_PNG: (
        b"\x89PNG\r\n\x1a\nFAKE_PNG_BYTES_FOR_ELITEA_1841_TEST",
        "image/png",
    ),
    FILE_TXT: (
        b"Sample content for ELITEA-1841 select-all ZIP test - sample.txt\n",
        "text/plain",
    ),
}

EXPECTED_ZIP_NAMELIST_SET = set(SEEDED_FILES.keys())

# Artificial per-request delay (seconds) applied ONLY to this test's
# artifact-download GETs, via page.route() — a legitimate timing-control
# technique (delays a network response, not a synthetic input event), not
# defect masking. With 6 small files the real flow completes too fast to
# reliably observe the FULL progress sequence without it (AFS § Automation
# Hints — same 600ms value the analyst confirmed reliable).
ROUTE_DELAY_SECONDS = 0.6

# Poll interval (seconds) for sampling the progress dialog's trio while it
# is visible — same 150ms value the AFS's analyst pass confirmed reliable
# for catching every distinct counter frame.
POLL_INTERVAL_SECONDS = 0.15

PROGRESS_FRAME_RE = re.compile(r"^(\d+) of (\d+) files$")


def _delayed_route(route):
    time.sleep(ROUTE_DELAY_SECONDS)
    route.continue_()


def _poll_zip_progress_frames(artifacts_page: ArtifactsPage) -> list[dict]:
    """Poll the counter/progress-bar/current-file trio while the ZIP dialog
    is visible, collecting one frame per DISTINCT counter value observed
    (in first-seen order).

    Deliberately tolerant of the harmless "0 of 0 files"/``valuenow="NaN"``
    reset frame that fires for one tick immediately before the dialog
    unmounts (AFS § Automation Hints, confirmed live by the analyst) — such
    frames don't match ``PROGRESS_FRAME_RE`` and are silently skipped, never
    recorded as a captured frame.

    Returns:
        List of ``{"current": int, "total": int, "valuenow": str | None,
        "current_file": str}`` dicts, one per distinct counter value.
    """
    frames: list[dict] = []
    seen_currents: set[int] = set()
    deadline = time.monotonic() + (MAX_POLL_DURATION_MS / 1000)

    while time.monotonic() < deadline:
        try:
            if not artifacts_page.zip_download_progress_dialog.is_visible():
                break
            counter_text = (
                artifacts_page.zip_download_progress_counter.text_content() or ""
            ).strip()
            match = PROGRESS_FRAME_RE.match(counter_text)
            if match:
                current = int(match.group(1))
                if current not in seen_currents:
                    valuenow = artifacts_page.zip_download_progress_bar.get_attribute(
                        "aria-valuenow"
                    )
                    current_file_text = (
                        artifacts_page.zip_download_progress_current_file.text_content()
                        or ""
                    ).strip()
                    frames.append(
                        {
                            "current": current,
                            "total": int(match.group(2)),
                            "valuenow": valuenow,
                            "current_file": current_file_text,
                        }
                    )
                    seen_currents.add(current)
        except Exception as exc:
            # Transient DOM read during a re-render — skip this sample, keep polling.
            logger.debug("Progress-frame poll sample skipped: %s", exc)
        time.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Captured %d distinct progress frame(s): %s", len(frames), frames)
    return frames


@allure.epic("Artifacts")
@allure.feature("Download Flow")
class TestArtifactDownloadAllFilesSelectAllZip:
    """ELITEA-1841 — Download all files via the header "Select all"
    checkbox as a ZIP, with full progress-sequence verification.

    Verifies the header checkbox's own state transition (a brand-new,
    previously-unexercised element), the invariant toolbar tooltip, the
    FULL 1-to-6 progress sequence, and that the resulting ZIP contains
    exactly the seeded files, flattened to the ZIP root, byte-identical to
    what was seeded, and CRC-clean.
    """

    @pytest.mark.p1
    @allure.title(
        "Clicking the header 'Select all' checkbox and 'Download files' "
        "downloads all files as a ZIP with a full progress sequence"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1841_download-flow-all-files-select-all-checkbox-zip.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.flaky
    def test_download_all_files_via_select_all_as_zip(
        self, page, artifact_api, artifact_bucket,
    ):
        """Selecting all files via the header checkbox and clicking
        'Download files' produces a ZIP.

        Read-only from the bucket's perspective at the end: the bucket is
        mutated exactly once (seeded with the 6 case files under ``a1/``) —
        the minimal state this observable inherently requires (workflow
        skill Hard Rule 10) — then every assertion reads that state without
        further mutation.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # Delay ONLY the single-file artifact-download GETs — scoped to
        # this test's own page instance, not a global/shared config.
        page.route("**/artifact/default/**", _delayed_route)

        # ------------------------------------------------------------------
        # Precondition — seed all 6 case files under a1/ into the fresh
        # bucket via API (ArtifactAPI.upload_file — auto-creates the 'a1'
        # folder node; no separate folder-creation call exists or is needed,
        # confirmed live per the AFS).
        # ------------------------------------------------------------------
        for filename, (content, content_type) in SEEDED_FILES.items():
            artifact_api.upload_file(
                bucket_name, f"{FOLDER_NAME}/{filename}", content,
                content_type=content_type,
            )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate directly to the bucket's 'a1' subfolder "
            "(folds AFS Test Steps 1-2: Artifacts page load, bucket/"
            "subfolder selection, file-table visibility, and the toolbar "
            "download button's initial disabled state into one navigation, "
            "same folding precedent as ELITEA-1840); verify all 6 seeded "
            "files are listed and the toolbar download button starts "
            "disabled (0 selected)"
        ):
            artifacts_page.navigate_to_bucket_folder(
                bucket_name, FOLDER_NAME, timeout=NAVIGATION_TIMEOUT,
            )
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert set(file_names) == EXPECTED_ZIP_NAMELIST_SET, (
                f"Expected exactly the 6 seeded files, got {file_names}"
            )
            file_count = artifacts_page.get_total_file_count_from_pagination()
            assert file_count == 6, f"Expected pagination to read 6 total files, got {file_count}"
            expect(artifacts_page.download_files_button).to_be_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 2 — Click the header 'Select all' checkbox; verify all 6 "
            "file rows become checked (queried independently, not just "
            "assumed) AND the header checkbox itself lands fully-checked, "
            "non-indeterminate"
        ):
            artifacts_page.click_select_all_checkbox(timeout=UI_ELEMENT_TIMEOUT)

            checkbox_states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert all(checkbox_states.values()), (
                f"Expected all 6 rows checked after one header-checkbox click, "
                f"got: {checkbox_states}"
            )
            assert len(checkbox_states) == 6, (
                f"Expected exactly 6 rows queried, got {len(checkbox_states)}: {checkbox_states}"
            )

            assert artifacts_page.is_select_all_checkbox_checked(timeout=UI_ELEMENT_TIMEOUT), (
                "Header 'Select all' checkbox should be Mui-checked after selecting all rows"
            )
            assert not artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), (
                "Header 'Select all' checkbox should NOT be indeterminate when all "
                "6 rows are selected (0->6 via one click lands directly in the "
                "fully-checked state)"
            )

        with allure.step(
            "Step 3 — Verify the toolbar 'Download files' button transitions "
            "from disabled to enabled, with tooltip text exactly "
            "'Download files' (invariant across partial/full selection, "
            "unlike the delete button's tooltip)"
        ):
            expect(artifacts_page.download_files_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )
            tooltip_text = artifacts_page.get_download_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == "Download files", (
                f"Expected static tooltip text 'Download files', got {tooltip_text!r}"
            )

        with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as download_info:
            with allure.step("Step 4 — Click the toolbar 'Download files' button"):
                artifacts_page.download_files_button.click()

            with allure.step(
                "Step 5 — Verify the ZIP-preparation dialog appears with the "
                "correct title, a determinate progress bar, a file counter, "
                "a current-file label, and a visible Cancel button"
            ):
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

            with allure.step(
                "Step 6 — Verify the counter, current-file label, and "
                "progress bar advance through the FULL range as each of the "
                "6 files is processed (the differentiator from ELITEA-1840's "
                "single-frame spot-check) — polled via a network-delayed "
                "route while the dialog is visible"
            ):
                frames = _poll_zip_progress_frames(artifacts_page)

                assert frames, "Expected at least one valid progress frame to be captured"
                currents = [f["current"] for f in frames]
                assert all(f["total"] == 6 for f in frames), (
                    f"Every captured frame should read total=6, got: {frames}"
                )
                assert currents == sorted(currents), (
                    f"Progress counter should be non-decreasing across the "
                    f"captured sequence, got: {currents}"
                )
                # A brief "0 of 6" precursor frame (total already known, no
                # file completed yet) is a legitimate initial render state —
                # confirmed live this run, distinct from the harmless
                # "0 of 0"/valuenow="NaN" TEARDOWN reset the AFS separately
                # documents (that one carries total=0, not 6, and is
                # filtered out by PROGRESS_FRAME_RE never matching it).
                # Case step 9's "starting at 1 of 6 files" is satisfied by
                # the sequence CONTAINING that frame, not requiring it be
                # literally the first captured sample.
                assert 1 in currents, (
                    f"Expected the progress sequence to include the "
                    f"'1 of 6 files' frame (case step 9), got: {currents}"
                )
                assert currents[-1] == 6, (
                    f"Expected the progress sequence to end at '6 of 6 files' "
                    f"(case step 10), got: {currents}"
                )
                assert len(set(currents)) >= 3, (
                    f"Expected a genuinely multi-frame sequence (not a single "
                    f"spot-check), got only {len(set(currents))} distinct "
                    f"frame(s): {currents}"
                )

                final_frame = frames[-1]
                assert final_frame["current"] == 6 and final_frame["valuenow"] == "100", (
                    f"Final captured frame should read '6 of 6 files' with "
                    f"aria-valuenow='100', got: {final_frame}"
                )
                # The current-file label is conditionally rendered — absent
                # until the first file is actually in flight (ArtifactsPage's
                # zip_download_progress_current_file docstring) — so the
                # precursor "0 of 6" frame (if captured) legitimately has no
                # label yet. Only frames where at least one file has started
                # (current >= 1) are required to show it.
                frames_with_file = [f for f in frames if f["current"] >= 1]
                assert frames_with_file, "Expected at least one frame with current >= 1"
                for frame in frames_with_file:
                    assert frame["current_file"].startswith(f"Current: {FOLDER_NAME}/"), (
                        f"Current-file label should show the FULL relative key "
                        f"including the '{FOLDER_NAME}/' subfolder prefix, got: "
                        f"{frame['current_file']!r}"
                    )

        download = download_info.value

        with allure.step(
            "Step 7 — Verify the dialog auto-closes and the ZIP downloads "
            "with the exact filename '{bucket}.zip'"
        ):
            expect(artifacts_page.zip_download_progress_dialog).to_be_hidden(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert download.suggested_filename == f"{bucket_name}.zip", (
                f"Expected ZIP filename '{bucket_name}.zip', got "
                f"'{download.suggested_filename}'"
            )

        downloaded_path = download.path()
        assert downloaded_path is not None, "Download should have completed to a local path"

        with allure.step(
            "Step 8 — Verify the ZIP's namelist is exactly the 6 seeded "
            "file names, flattened to the ZIP root (not nested under "
            f"'{FOLDER_NAME}/')"
        ):
            with zipfile.ZipFile(downloaded_path) as zf:
                namelist = zf.namelist()
            assert set(namelist) == EXPECTED_ZIP_NAMELIST_SET, (
                f"Expected ZIP namelist exactly {sorted(EXPECTED_ZIP_NAMELIST_SET)}, "
                f"got {sorted(namelist)}"
            )
            assert len(namelist) == 6, f"Expected exactly 6 ZIP entries, got {len(namelist)}"

        with allure.step(
            "Step 9 — Verify all 6 files are accessible and not corrupted "
            "inside the ZIP: each entry's bytes are byte-identical to the "
            "seeded content, and zipfile.testzip() returns None (CRC-clean)"
        ):
            with zipfile.ZipFile(downloaded_path) as zf:
                for filename, (content, _content_type) in SEEDED_FILES.items():
                    assert zf.read(filename) == content, (
                        f"'{filename}' ZIP entry content should be byte-identical "
                        "to the seeded content"
                    )
                bad_entry = zf.testzip()
                assert bad_entry is None, (
                    f"Expected zipfile.testzip() to return None (CRC-clean), "
                    f"but entry {bad_entry!r} failed its CRC check"
                )

        with allure.step(
            "Pass criterion — no console errors occurred anywhere across "
            "the select-all + download + ZIP-verification flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the select-all ZIP "
                f"download flow: {[m.text for m in console_errors]}"
            )
