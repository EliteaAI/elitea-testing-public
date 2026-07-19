"""UI Test for ELITEA-1824 — Upload Files to Bucket Subfolder via Three
Upload Options and Verify Bucket Selection and Contents.

Regression test: verifies all three upload entry points (the CENTER
empty-state button, the TOOLBAR upload icon, and the bucket 3-dot menu's
"Upload files" item) drive the identical underlying "Upload files to ..."
dialog / ``PUT /artifacts/s3/{bucket}/{key}`` mechanism, that uploaded files
land in the correct bucket/subfolder locations, and that the left-panel
tree + main-panel breadcrumb + URL stay in sync with bucket/folder
selection — including the ``data-selected`` state attribute added for this
case.

Known defect (github.com/EliteaAI/elitea-testing-public#649): the bucket
3-dot-menu "Upload files" entry point does not reset its default Path to
the bucket root — it inherits whatever subfolder the user was last
navigated into (root cause: shared ``currentPrefix`` state in
``useFileUpload.hooks.js``, never reset for this entry point). This is an
ISOLATED defect (the rest of the 46-step case passes cleanly) — asserted
with ``expect.soft()`` per this project's no-masking policy (sanctioned-RED
exception, ``.agents/testing.md`` § Merge gate), then worked around (clear
the Path field) so every downstream step still runs against a clean state.

Two CLARIFICATIONs (case-text drift, not defects — reverse-masking guard):
- #650: the bucket-menu dropdown's item is labelled "Rename", not "Edit"
  as the case text says (same functional slot, intentional relabel).
- #651: a single click on the bucket's own row TOGGLES expand/collapse
  rather than unconditionally expanding when the bucket is already the
  active node — deterministic sequencing used below (click, check the a1
  tree item's visibility, click again if not yet expanded).

Test flow:
1. Seed a fresh, empty bucket via the ``artifact_bucket`` fixture.
2-3. Select the bucket; verify the empty state (center "Upload files"
   button) is shown.
4-11. Upload sample.txt via the CENTER empty-state button, into a
   manually-typed "a1" subfolder — verify the PUT, the toast, the tree,
   and the breadcrumb.
12. Verify sample.txt's row metadata (Name/Type/Size/Last-update).
13-18. Upload sample.png via the TOOLBAR icon — Path is pre-filled
   "{bucket}/a1/" (inherited, unchanged) — verify the PUT, the toast, and
   both files listed together.
19-26. Upload sample.md via the bucket 3-dot menu — the Path field
   incorrectly inherits "{bucket}/a1/" instead of resetting to bucket root
   (KNOWN DEFECT #649, soft-asserted), worked around by clearing the field
   before uploading — verify the PUT lands at bucket root, the toast, and
   the breadcrumb reverting to root.
27. Verify sample.md is listed at bucket root.
28-33. Click the bucket's own row (toggle, CLARIFICATION #651); verify
   selected state + tree expansion; click into the a1 subfolder; verify
   selected state, breadcrumb, URL, and exact file-set (sample.txt +
   sample.png, NOT sample.md).
34-37. Click the bucket's own row again (root level); verify the URL loses
   the folder param, the breadcrumb reverts, sample.md is visible at root.

AFS: test-specs/artifacts/l2_upload-three-options-verify-selection_ELITEA-1824.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_three_options_verify_selection.py -v
"""

import logging
import re
import struct
import urllib.parse
import zlib

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, toast, file rows
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions, bucket panel load
DIALOG_TIMEOUT = 10_000           # dialog open transitions
ABSENCE_CHECK_TIMEOUT = 3_000     # short wait for an element expected NOT to appear
TOGGLE_SETTLE_TIMEOUT = 2_000     # short poll after a toggle click, before retrying it

# AFS § Test Data viewport note (same finding as ELITEA-1808/1826): the
# "Last update" column is present in the DOM but visually clipped/hidden
# below ~1600px viewport width — set explicitly before asserting it.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

SUBFOLDER = "a1"

TXT_FILE_NAME = "sample.txt"
TXT_FILE_CONTENT = b"Sample text content for the ELITEA-1824 three-options upload test.\n"

MD_FILE_NAME = "sample.md"
MD_FILE_CONTENT = b"# Sample Markdown\n\nContent for the ELITEA-1824 three-options upload test.\n"

PNG_FILE_NAME = "sample.png"

SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"

# Confirmed live (AFS § Test Data): "DD-MM-YYYY, HH:MM AM/PM". Pattern only,
# never an exact value — the clock differs per run.
LAST_UPDATE_TIMESTAMP_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)")


def _minimal_png_bytes() -> bytes:
    """Build a valid, minimal 1x1 PNG in memory.

    Reused technique from ``test_artifacts_upload_duplicate_cancel.py:75-91``
    (ELITEA-1832), same as ELITEA-1826's own precedent
    (``test_artifacts_upload_multiple_files.py``) — content is irrelevant to
    this case's assertions beyond being a well-formed PNG the OS file picker
    accepts and that renders as "PNG Image" in the Type column.
    """
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def _url_query_params(url: str) -> dict[str, str]:
    """Return ``{param: value}`` for a URL's query string (last value wins).

    Small local helper (not page-object state — pure string parsing, no
    locator) used to assert the ``bucket``/``folder`` URL params precisely,
    same technique already established in
    :meth:`ArtifactsPage.navigate_to_bucket_folder`'s own race-check.
    """
    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    return {k: v[-1] for k, v in parsed.items()}


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Three Entry Points + Bucket/Folder Selection")
class TestArtifactsUploadThreeOptionsVerifySelection:
    """ELITEA-1824 — Upload via all three entry points; verify tree/breadcrumb/URL sync.

    Bucket is the test's own mutation (via ``artifact_bucket``, deleted in
    its own teardown — known pre-existing defect #636 means the delete call
    may 404 and the bucket may leak, out of scope here) — the minimal state
    this observable inherently requires (workflow skill Hard Rule 10): the
    case's own subject IS uploading into/selecting a specific multi-file,
    multi-folder bucket state, so there is no pre-existing stable bucket to
    assert against read-only.
    """

    @pytest.mark.p1
    @allure.title(
        "Upload via all three entry points and verify bucket/folder tree, "
        "breadcrumb, and URL selection sync"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1824_upload-files-via-three-options-verify-selection.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/649",
        "Known defect #649 — bucket-menu upload doesn't reset path to root",
    )
    def test_upload_via_three_options_and_verify_selection(
        self, page, artifact_bucket, tmp_path,
    ):
        """Upload sample.txt/.png/.md via 3 entry points; verify selection stays synced.

        The one known-defect step (bucket-menu Path pre-fill, #649) is
        ``expect.soft()``-asserted against the case's documented CORRECT
        expected value (bucket root) — confirmed live to fail today — then
        worked around so steps 24-37 still verify a clean end state.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # AFS § Test Data viewport note — set explicitly so the "Last
        # update" timestamp column is actually in view before asserting it.
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})

        txt_path = tmp_path / TXT_FILE_NAME
        txt_path.write_bytes(TXT_FILE_CONTENT)
        png_path = tmp_path / PNG_FILE_NAME
        png_bytes = _minimal_png_bytes()
        png_path.write_bytes(png_bytes)
        md_path = tmp_path / MD_FILE_NAME
        md_path.write_bytes(MD_FILE_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()

        with allure.step("Step 2 — Verify the fixture-created bucket is visible in the bucket list"):
            artifacts_page.wait_for_bucket_in_list(bucket_name, timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            "Steps 3-4 — Click the bucket in the list; verify the empty state "
            "('No files in this bucket' + center 'Upload files' button) is shown"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.is_bucket_empty(), (
                f"Precondition: bucket '{bucket_name}' should be empty before any upload"
            )

        with allure.step(
            "Steps 5-8 — Click the CENTER 'Upload files' button (native file "
            "explorer opens immediately); select sample.txt; confirm the "
            "selection (one mechanically inseparable Playwright action — "
            "expect_file_chooser() would raise if the explorer never opened)"
        ):
            artifacts_page.upload_files_via_empty_state([str(txt_path)])

        with allure.step(
            "Step 9 — Verify the 'Upload files to ...' modal opens with the "
            "Path field pre-filled with the bucket root"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_normalized_prefix()
            assert path_text == f"{bucket_name}/", (
                f"Path field should be pre-filled with the bucket-root prefix "
                f"'{bucket_name}/', got: {path_text!r}"
            )

        with allure.step(
            "Step 10 — Append '/a1' to the Path field; verify the combined "
            "path reads '{bucket}/a1'"
        ):
            # Click+type on the dedicated input-field testid, not the outer
            # wrapper — confirmed live (ELITEA-1824 implementer Phase 2
            # exploration): with a long bucket name, the read-only
            # bucket/currentPrefix startAdornment can occupy most of the
            # field's width, so a center-click on the WRAPPER can miss the
            # actual editable <input> entirely (0 characters land). Clicking
            # the input's own testid removes that ambiguity.
            artifacts_page.upload_path_input_field.click()
            artifacts_page.upload_path_input_field.type(SUBFOLDER)
            expect(artifacts_page.upload_path_input_field).to_have_value(
                SUBFOLDER, timeout=UI_ELEMENT_TIMEOUT,
            )
            # Combined text = the read-only prefix (unchanged by typing) +
            # the typed suffix — two separate DOM elements (ELITEA-1824
            # implementer Phase 2 finding: a native <input>'s value is never
            # part of any ancestor's text_content()), read via the dedicated
            # artifacts-upload-path-input-field testid added for this case.
            path_text = artifacts_page.get_upload_path_combined_text()
            assert path_text == f"{bucket_name}/{SUBFOLDER}", (
                f"Path field should read '{bucket_name}/{SUBFOLDER}' after "
                f"appending the subfolder, got: {path_text!r}"
            )

        with allure.step(
            "Step 11 — Click Upload; verify the PUT to a1/sample.txt returns 200 OK"
        ):
            upload_response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert upload_response.status == 200, (
                f"Upload PUT should return 200, got: {upload_response.status} "
                f"for {upload_response.url}"
            )
            assert f"{bucket_name}/{SUBFOLDER}/{TXT_FILE_NAME}" in upload_response.url, (
                f"Upload PUT URL should target '{bucket_name}/{SUBFOLDER}/"
                f"{TXT_FILE_NAME}', got: {upload_response.url}"
            )

        with allure.step("Step 12 — Verify the success notification"):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step("Step 13 — Verify subfolder a1 appears under the bucket in the left panel"):
            artifacts_page.wait_for_file_in_tree(f"{SUBFOLDER}/", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 14 — Verify the main-panel breadcrumb shows '{bucket} > a1'"):
            assert artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT) == bucket_name, (
                f"Breadcrumb bucket label should read '{bucket_name}'"
            )
            assert artifacts_page.get_breadcrumb_folder_names(timeout=UI_ELEMENT_TIMEOUT) == [SUBFOLDER], (
                f"Breadcrumb should show exactly one folder crumb: {SUBFOLDER!r}"
            )

        with allure.step(
            "Step 15 — Verify sample.txt is listed with Name/Type/Size/Last-update populated"
        ):
            txt_row = artifacts_page.get_file_row_text(TXT_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Text" in txt_row, (
                f"'{TXT_FILE_NAME}' row should show Type 'Text', row text was: {txt_row!r}"
            )
            expected_txt_size = f"{len(TXT_FILE_CONTENT)} B"
            assert expected_txt_size in txt_row, (
                f"'{TXT_FILE_NAME}' row should show Size {expected_txt_size!r}, "
                f"row text was: {txt_row!r}"
            )
            assert LAST_UPDATE_TIMESTAMP_PATTERN.search(txt_row), (
                f"'{TXT_FILE_NAME}' row should show a 'Last update' timestamp "
                f"matching DD-MM-YYYY, HH:MM AM/PM, row text was: {txt_row!r}"
            )

        with allure.step(
            "Steps 16-19 — Click the TOOLBAR 'Upload files' icon (native file "
            "explorer opens immediately); select sample.png; confirm the selection"
        ):
            artifacts_page.upload_files([str(png_path)])

        with allure.step(
            "Steps 20-21 — Verify the 'Upload files to ...' modal opens with "
            "the Path field pre-filled '{bucket}/a1/' (inherited/unchanged "
            "from the currently-navigated subfolder — no edit needed)"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_normalized_prefix()
            assert path_text == f"{bucket_name}/{SUBFOLDER}/", (
                f"Path field should be pre-filled '{bucket_name}/{SUBFOLDER}/' "
                f"(carried over from the current folder), got: {path_text!r}"
            )

        with allure.step(
            "Step 22 — Click Upload; verify the PUT to a1/sample.png returns 200 OK"
        ):
            upload_response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert upload_response.status == 200, (
                f"Upload PUT should return 200, got: {upload_response.status} "
                f"for {upload_response.url}"
            )
            assert f"{bucket_name}/{SUBFOLDER}/{PNG_FILE_NAME}" in upload_response.url, (
                f"Upload PUT URL should target '{bucket_name}/{SUBFOLDER}/"
                f"{PNG_FILE_NAME}', got: {upload_response.url}"
            )

        with allure.step("Step 23 — Verify the success notification"):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 24 — Verify sample.png is listed alongside sample.txt in the "
            "'{bucket} > a1' view"
        ):
            assert set(artifacts_page.get_file_names()) == {TXT_FILE_NAME, PNG_FILE_NAME}, (
                f"Expected both files in the a1 view, got: "
                f"{set(artifacts_page.get_file_names())}"
            )
            assert artifacts_page.get_total_file_count_from_pagination() == 2, (
                "Expected exactly 2 files in the a1 view after both uploads"
            )

        with allure.step(
            "Steps 25-26 — Hover the bucket's own row and open its 3-dot "
            "actions menu — verify 'Upload files' item visible (case says "
            "'Edit' where the live label is 'Rename' — CLARIFICATION #650, "
            "not asserted here: no testid exists for the other menu items)"
        ):
            artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.bucket_menu_upload_files_menuitem.is_visible(), (
                "'Upload files' item should be visible once the bucket row's "
                "dot-menu is open"
            )

        with allure.step(
            "Steps 27-29 — Click 'Upload files' in the bucket menu (native "
            "file explorer opens immediately); select sample.md; confirm the selection"
        ):
            artifacts_page.click_bucket_menu_upload_files_item(
                [str(md_path)], timeout=NAVIGATION_TIMEOUT,
            )

        with allure.step(
            "Steps 30-32 — Verify the Path field (KNOWN DEFECT #649: the "
            "bucket-menu entry point should default to the bucket root, but "
            "inherits the currently-navigated subfolder instead)"
        ):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            # Known defect: #649 — soft-assert the case's documented CORRECT
            # expected value (bucket root only, "{bucket_name}/"). Confirmed
            # live (AFS) this fails today: the actual value is
            # "{bucket_name}/a1/" because this entry point never resets the
            # shared `currentPrefix` state left behind by the earlier
            # subfolder navigation (Steps 5-24). Soft so the rest of the flow
            # (the corrected retry-from-root sequence below + all downstream
            # assertions) still runs — sanctioned-RED exception per
            # .agents/testing.md § Merge gate. Compared against the raw
            # text_content() shape (label + zero-width-space padding,
            # ELITEA-1824 finding — see get_upload_path_normalized_prefix())
            # since expect() needs the literal DOM text, not the stripped form.
            expect.soft(
                artifacts_page.upload_path_input,
                "Known defect: #649 — bucket-menu 'Upload files' should "
                "default to the bucket root, not the currently-navigated "
                "subfolder",
            ).to_have_text(f"Path​{bucket_name}/​", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 23 (AFS workaround — CORRECTED per implementer Phase 2 "
            "exploration) — the AFS's documented 'select_text()+Backspace' "
            "technique does not work: the buggy prefix lives in a READ-ONLY "
            "DOM node (UploadPathDialog.jsx's startAdornment, driven by the "
            "`currentPrefix` prop), not the editable input — confirmed live "
            "10x Backspace on the focused input produces zero change and the "
            "resulting upload still lands in a1/. The only way to clear the "
            "inherited state is to abandon this dialog and re-open it after "
            "`currentPrefix` itself has been reset by navigating to bucket "
            "root — same root-cause mechanism the AFS's own Known Defects "
            "section already documents (`currentPrefix` is read fresh each "
            "time the dialog's computeFullPath() runs)"
        ):
            artifacts_page.close_upload_path_dialog(timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_bucket_menu_upload_files_item(
                [str(md_path)], timeout=NAVIGATION_TIMEOUT,
            )
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            path_text = artifacts_page.get_upload_path_normalized_prefix()
            assert path_text == f"{bucket_name}/", (
                f"Path field should read the bucket-root prefix "
                f"'{bucket_name}/' once re-opened from bucket root (isolates "
                f"the #649 defect to stale currentPrefix reuse, same proof "
                f"technique as the AFS's own Known Defects isolation pass), "
                f"got: {path_text!r}"
            )

        with allure.step(
            "Step 33 — Click Upload; verify the PUT lands at the bucket ROOT "
            "(no a1/ prefix) and returns 200 OK — confirms the retry-from-root "
            "sequence succeeded"
        ):
            upload_response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert upload_response.status == 200, (
                f"Upload PUT should return 200, got: {upload_response.status} "
                f"for {upload_response.url}"
            )
            assert f"{bucket_name}/{MD_FILE_NAME}" in upload_response.url, (
                f"Upload PUT URL should target the bucket-root key "
                f"'{bucket_name}/{MD_FILE_NAME}', got: {upload_response.url}"
            )
            assert f"{SUBFOLDER}/{MD_FILE_NAME}" not in upload_response.url, (
                f"Upload PUT URL should NOT be nested under '{SUBFOLDER}/' "
                f"(that would mean the workaround failed), got: "
                f"{upload_response.url}"
            )

        with allure.step("Step 34 — Verify the success notification"):
            expect(artifacts_page.success_toast_message).to_have_text(
                SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 35 — Verify the main-panel breadcrumb shows the bucket "
            "root only, no subfolder suffix"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT) == bucket_name, (
                f"Breadcrumb bucket label should read '{bucket_name}'"
            )
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "Breadcrumb should show no folder crumbs at bucket root"
            )

        with allure.step("Step 36 — Verify sample.md is listed at the root level"):
            assert artifacts_page.file_exists(MD_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{MD_FILE_NAME}' should be visible at bucket root"
            )
            md_row = artifacts_page.get_file_row_text(MD_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert "Markdown" in md_row, (
                f"'{MD_FILE_NAME}' row should show Type 'Markdown', row text was: {md_row!r}"
            )

        with allure.step(
            "Step 37 — Click the bucket's own row in the left panel "
            "(CLARIFICATION #651: a single click on an already-active bucket "
            "row TOGGLES expand/collapse rather than unconditionally "
            "expanding — deterministic sequencing: click, check a1's tree "
            "item visibility, click again if not yet expanded)"
        ):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            if not artifacts_page.is_tree_item_visible(f"{SUBFOLDER}/", timeout=TOGGLE_SETTLE_TIMEOUT):
                artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 38 — Verify the bucket is selected/highlighted AND the "
            "tree shows subfolder a1"
        ):
            assert artifacts_page.is_bucket_selected(bucket_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Bucket '{bucket_name}' row should carry "
                f"data-selected=\"true\" while its root is the active view"
            )
            artifacts_page.wait_for_file_in_tree(f"{SUBFOLDER}/", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 39 — Click subfolder a1 in the left-panel tree; verify the "
            "URL reflects bucket + folder=a1"
        ):
            artifacts_page.click_tree_item(f"{SUBFOLDER}/", timeout=UI_ELEMENT_TIMEOUT)
            params = _url_query_params(page.url)
            assert params.get("bucket") == bucket_name and params.get("folder") == SUBFOLDER, (
                f"URL should reflect bucket={bucket_name!r} and "
                f"folder={SUBFOLDER!r}, got query params: {params} "
                f"(full URL: {page.url})"
            )

        with allure.step(
            "Step 40 — Verify a1 is highlighted AND the breadcrumb shows '{bucket} > a1'"
        ):
            assert artifacts_page.is_tree_item_selected(f"{SUBFOLDER}/", timeout=UI_ELEMENT_TIMEOUT), (
                f"Tree item '{SUBFOLDER}/' should carry data-selected=\"true\" "
                f"once navigated into"
            )
            assert artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT) == bucket_name, (
                f"Breadcrumb bucket label should read '{bucket_name}'"
            )
            assert artifacts_page.get_breadcrumb_folder_names(timeout=UI_ELEMENT_TIMEOUT) == [SUBFOLDER], (
                f"Breadcrumb should show exactly one folder crumb: {SUBFOLDER!r}"
            )

        with allure.step(
            "Step 41 — Verify the file table contains EXACTLY 2 files: "
            "sample.txt and sample.png"
        ):
            assert artifacts_page.get_total_file_count_from_pagination() == 2, (
                "Expected exactly 2 files in the a1 view"
            )
            assert set(artifacts_page.get_file_names()) == {TXT_FILE_NAME, PNG_FILE_NAME}, (
                f"Expected exactly {{'{TXT_FILE_NAME}', '{PNG_FILE_NAME}'}} in "
                f"the a1 view, got: {set(artifacts_page.get_file_names())}"
            )

        with allure.step("Step 42 — Verify sample.md is NOT listed in the a1 view"):
            assert not artifacts_page.file_exists(MD_FILE_NAME, timeout=ABSENCE_CHECK_TIMEOUT), (
                f"'{MD_FILE_NAME}' should NOT appear while viewing the a1 subfolder"
            )

        with allure.step(
            "Step 43 — Click the bucket's own row (root level) in the left "
            "panel; verify the URL loses the folder param"
        ):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            params = _url_query_params(page.url)
            assert params.get("bucket") == bucket_name and "folder" not in params, (
                f"URL should reflect bucket={bucket_name!r} with no folder "
                f"param, got query params: {params} (full URL: {page.url})"
            )

        with allure.step("Step 44 — Verify the breadcrumb shows the bucket root only"):
            assert artifacts_page.get_breadcrumb_bucket_text(timeout=UI_ELEMENT_TIMEOUT) == bucket_name, (
                f"Breadcrumb bucket label should read '{bucket_name}'"
            )
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "Breadcrumb should show no folder crumbs at bucket root"
            )

        with allure.step("Step 45 — Verify sample.md is listed at the root level"):
            assert artifacts_page.file_exists(MD_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{MD_FILE_NAME}' should be visible at bucket root"
            )

        with allure.step(
            "Step 46 — Verify the URL reflects the currently-selected bucket "
            "and folder path (root — no folder param, matches Step 43's own check)"
        ):
            params = _url_query_params(page.url)
            assert params.get("bucket") == bucket_name and "folder" not in params, (
                f"Final URL should reflect bucket={bucket_name!r} with no "
                f"folder param, got query params: {params} (full URL: {page.url})"
            )

        with allure.step(
            "Side-channel check — no console errors across the full "
            "navigate → 3x-upload → tree/breadcrumb/URL selection flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the three-options upload "
                f"flow: {[m.text for m in console_errors]}"
            )
