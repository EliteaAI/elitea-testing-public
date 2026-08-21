"""UI Test for ELITEA-1834 — Upload Flow: File Uploaded to the Selected
Subfolder When Using the Bucket Actions Button.

Regression test: with subfolder ``a1`` selected in the left-panel tree, the
bucket 3-dot ("Bucket actions") menu's "Upload files" item opens the
"Upload files to ..." dialog pre-filled with ``{bucket}/a1/``; uploading from
that dialog PUTs the file to ``.../{bucket}/a1/sample.txt``, toasts success,
leaves the main panel on ``{bucket} > a1``, lists the file inside ``a1`` —
and NOT at the bucket root.

Contradiction the reader must know about (do not "fix" this test to match
the neighbouring spec):
  - This case (ELITEA-1834) states the bucket-menu upload dialog SHOULD
    pre-fill the currently-selected subfolder (``{bucket}/a1/``). The live
    product does exactly that, so it is asserted here as CORRECT, with hard
    assertions.
  - The merged spec ``test_artifacts_upload_three_options_verify_selection.py``
    (ELITEA-1824) soft-asserts the OPPOSITE expected value against the same
    DOM node, as KNOWN DEFECT
    https://github.com/EliteaAI/elitea-testing-public/issues/649 — that case
    says the same entry point should reset to the bucket root.
  - One machine state, two case texts with opposite expectations
    (``Artifacts.jsx``'s single ``currentPrefix``, never reset by
    ``BucketItem.jsx``'s ``handleUploadClick``, rendered by
    ``UploadPathDialog.jsx``). Filed for a human ruling as CLARIFICATION
    https://github.com/EliteaAI/elitea-testing-public/issues/1629. Per the
    reverse-masking guard the live contract is asserted here; if #1629 is
    resolved in favour of #649, steps 12-18 need RE-ANALYSIS, never a
    silent weakening.

Two further CLARIFICATIONs already tracked and relevant to the sequencing:
  - #650: the bucket menu's item is labelled "Rename", not "Edit". This case
    only requires "Upload files" to be present, so only that item is
    asserted.
  - #651: a click on an ALREADY-selected bucket row TOGGLES tree
    expand/collapse — so bucket-row clicks below are guarded by a
    post-condition check plus a conditional second click, never assumed.

Test flow:
Setup (transit, not case steps) — a fresh bucket via the ``artifact_bucket``
fixture, then subfolder ``a1/`` created by a REAL UI upload of ``seed.txt``
through the empty-state entry point with "a1" typed into the Path field
(``a1/`` is an S3 key prefix; there is no "create folder" UI). ``seed.txt``
deliberately is NOT named ``sample.txt`` — a name collision inside ``a1``
would raise the "Resolve duplicates" dialog and derail step 11.
1-2. Navigate to Artifacts; select the bucket and confirm ``a1/`` is shown.
3-5. Select ``a1``; verify exclusive selection, breadcrumb and URL.
6-7. Open the bucket's 3-dot menu; verify "Upload files" is present.
8-11. Click it (the native file chooser fires on the click), select
   ``sample.txt``; the "Upload files to ..." dialog opens.
12-13. Verify the Path prefix is ``{bucket}/a1/`` with nothing pre-typed, and
   the dialog description names that same target.
14-15. Upload — verify the PUT's URL/status and the success toast.
16-18. Verify the view stays on ``{bucket} > a1``, ``sample.txt`` is listed
   there (table + left tree), and the bucket ROOT listing holds only the
   ``a1`` folder.

Substitution declared (fidelity): the ONLY substitutions are transit — the
bucket is created via the artifacts API (``artifact_bucket`` fixture; the
case's precondition merely requires it to exist) and ``a1/`` is seeded by a
real UI upload. Nothing is faked: every asserted observable (path prefix,
description string, PUT URL/status, toast, breadcrumb, URL, tree state, both
listings) is produced by the running product.

AFS: test-specs/artifacts/l2_upload-flow-file-uploaded-to-selected-subfolder-via-bucket-actions_ELITEA-1834.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority)
    - new: added on automation/base, not yet validated on a deployed env

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_upload_to_selected_subfolder.py -v
"""

import logging
import re

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.p2, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # buttons, panels, form fields
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions / file chooser
DIALOG_TIMEOUT = 10_000           # dialog open/close transitions
TABLE_REFETCH_TIMEOUT = 15_000    # file table refetch after a backend write

# The file table's "Last update" column clips below ~1600 px (test-specs/
# artifacts/_surface.md) — the same viewport every sibling artifacts spec
# pins. Load-bearing here: step 17 reads that column.
VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

SUBFOLDER = "a1"
SUBFOLDER_KEY = "a1/"             # tree/S3 keys carry the trailing slash
SEED_FILE_NAME = "seed.txt"       # transit only — exists so `a1/` exists
SEED_CONTENT = b"ELITEA-1834 seed content, creates the a1/ prefix.\n"
UPLOAD_FILE_NAME = "sample.txt"   # the case's own subject
UPLOAD_CONTENT = b"ELITEA-1834 sample content\n"
SUCCESS_TOAST_TEXT = "Your file(s) have been successfully uploaded!"

# Matches ArtifactTable.jsx's ARTIFACT_TABLE_CONFIG.DATE_FORMAT
# ('dd-MM-yyyy, hh:mm a'). The "Last update" column has no per-cell testid
# (ArtifactTable renders data cells through the shared, generic
# GridTableRowDataCell), so the row's rendered value is matched on the row's
# full text — the established, merged, testid-compliant pattern
# (test_artifacts_upload_duplicate_replace.py), never a new raw locator.
LAST_UPDATE_TIMESTAMP_RE = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} [AP]M")


@allure.epic("Artifacts")
@allure.feature("Upload Flow — Bucket Actions Menu")
class TestArtifactUploadToSelectedSubfolder:
    """ELITEA-1834 — bucket-menu upload targets the selected subfolder.

    Verifies the "Upload files to ..." dialog opened from the bucket
    3-dot menu pre-fills ``{bucket}/a1/`` while ``a1`` is selected, and that
    the uploaded file lands in ``a1`` — not at the bucket root.
    """

    @pytest.mark.p2
    @allure.title(
        "Bucket-actions 'Upload files' pre-fills the selected subfolder and "
        "the file is uploaded into that subfolder, not the bucket root"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1834_upload-flow-file-uploaded-to-selected-subfolder.md",
        "onetest-ai Test Case link",
    )
    def test_upload_via_bucket_actions_lands_in_selected_subfolder(
        self, page, artifact_bucket, tmp_path,
    ):
        """Upload through the bucket-actions menu lands in the selected subfolder.

        Substitution declared: the bucket is created via the artifacts API
        (``artifact_bucket`` fixture) and subfolder ``a1/`` is seeded by a
        real UI upload — both transit only, reaching the case's stated
        precondition. Every asserted observable is produced by the product.

        The Path-prefix assertion (step 12) asserts ``{bucket}/a1/`` as
        CORRECT per this case; see the module docstring for the #649/#1629
        contradiction with ELITEA-1824's opposite expectation.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        seed_file_path = tmp_path / SEED_FILE_NAME
        seed_file_path.write_bytes(SEED_CONTENT)
        upload_file_path = tmp_path / UPLOAD_FILE_NAME
        upload_file_path.write_bytes(UPLOAD_CONTENT)

        # ------------------------------------------------------------------
        # Setup (preconditions, not case steps) — create subfolder `a1/` by
        # uploading seed.txt through the empty-state entry point with "a1"
        # typed into the Path field. A real product action; `a1/` is an S3
        # key prefix, there is no "create folder" UI.
        # ------------------------------------------------------------------
        with allure.step(
            f"Precondition — seed subfolder '{SUBFOLDER_KEY}' in bucket "
            f"'{bucket_name}' by uploading {SEED_FILE_NAME} into it"
        ):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.upload_files_via_empty_state(
                [str(seed_file_path)], timeout=NAVIGATION_TIMEOUT,
            )
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            artifacts_page.fill_upload_path(SUBFOLDER, timeout=UI_ELEMENT_TIMEOUT)
            seed_response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert seed_response.status == 200, (
                f"Seeding upload should return 200, got {seed_response.status} "
                f"for {seed_response.url}"
            )
            assert f"{bucket_name}/{SUBFOLDER_KEY}{SEED_FILE_NAME}" in seed_response.url, (
                "Seeding upload should PUT to the a1/ prefix so the subfolder "
                f"exists; got {seed_response.url}"
            )

        with allure.step("Step 1 — Navigate to the Artifacts section"):
            artifacts_page.navigate_to_artifacts()
            artifacts_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)

        with allure.step(
            f"Step 2 — Click bucket '{bucket_name}' in the bucket list; the "
            f"tree expands showing subfolder '{SUBFOLDER}'"
        ):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            if not artifacts_page.is_tree_item_visible(SUBFOLDER_KEY, timeout=5000):
                # CLARIFICATION #651 — a click on an already-selected bucket
                # row TOGGLES the tree rather than unconditionally expanding
                # it. Deterministic sequencing: check, then click again.
                logger.info("Tree not expanded after first click — clicking bucket row again")
                artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)

            assert artifacts_page.is_bucket_selected(bucket_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Bucket '{bucket_name}' should carry data-selected=\"true\" "
                "after its row is clicked"
            )
            assert artifacts_page.is_tree_item_visible(SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT), (
                f"Subfolder '{SUBFOLDER}' should be visible in the left-panel "
                f"tree once bucket '{bucket_name}' is expanded"
            )
            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "The bucket should open at its ROOT — no folder crumbs yet"
            )

        with allure.step(f"Step 3 — Click subfolder '{SUBFOLDER}' to select it"):
            artifacts_page.click_tree_item(SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 4 — Verify '{SUBFOLDER}' is highlighted (selected) in the "
            "left-panel tree, and that the selection is exclusive"
        ):
            assert artifacts_page.is_tree_item_selected(
                SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT
            ), (
                f"Tree node '{SUBFOLDER_KEY}' should carry data-selected=\"true\" "
                "once clicked"
            )
            assert not artifacts_page.is_bucket_selected(
                bucket_name, timeout=UI_ELEMENT_TIMEOUT
            ), (
                "Selection is exclusive: the bucket row must lose "
                'data-selected="true" once a subfolder is the selected node — '
                "that exclusivity is what makes the subfolder highlight meaningful"
            )

        with allure.step(
            f"Step 5 — Verify the main panel header shows '{bucket_name} > {SUBFOLDER}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, "Breadcrumb should name the selected bucket"
            assert artifacts_page.get_breadcrumb_folder_names() == [SUBFOLDER], (
                f"Breadcrumb should show exactly one folder crumb, '{SUBFOLDER}'"
            )
            assert f"folder={SUBFOLDER}" in page.url, (
                f"URL should carry the folder param for '{SUBFOLDER}', got {page.url}"
            )

        with allure.step(
            f"Steps 6-7 — Hover bucket '{bucket_name}' and open its 3-dot "
            "actions menu; the dropdown includes 'Upload files'"
        ):
            artifacts_page.hover_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(
                artifacts_page.bucket_menu_upload_files_menuitem,
                "'Upload files' should be present in the opened bucket-actions menu",
            ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Steps 8-10 — Click 'Upload files' (the native file chooser opens "
            f"immediately on the click) and select {UPLOAD_FILE_NAME}"
        ):
            # Playwright's expect_file_chooser fires ON the click — that event
            # IS the automatable form of case steps 8-9 ("system file explorer
            # opens immediately"); the OS dialog itself is not inspectable.
            artifacts_page.click_bucket_menu_upload_files_item(
                [str(upload_file_path)], timeout=NAVIGATION_TIMEOUT,
            )

        with allure.step("Step 11 — Verify the 'Upload files to ...' modal opens"):
            artifacts_page.wait_for_upload_path_dialog(timeout=DIALOG_TIMEOUT)
            expect(
                artifacts_page.upload_path_dialog,
                "The 'Upload files to ...' dialog should be visible after the "
                "file selection is confirmed",
            ).to_be_visible(timeout=DIALOG_TIMEOUT)

        with allure.step(
            f"Step 12 — Verify the Path field displays '{bucket_name}/{SUBFOLDER_KEY}' "
            "(the currently selected subfolder)"
        ):
            # ELITEA-1834's expected result, asserted as CORRECT — see the
            # module docstring for the #649/#1629 contradiction. Compared on
            # the NORMALIZED prefix: the raw text_content() carries the MUI
            # floating label plus zero-width-space padding.
            actual_prefix = artifacts_page.get_upload_path_normalized_prefix()
            assert actual_prefix == f"{bucket_name}/{SUBFOLDER_KEY}", (
                "The bucket-actions upload dialog should pre-fill the path with "
                f"the SELECTED subfolder '{bucket_name}/{SUBFOLDER_KEY}', got "
                f"{actual_prefix!r}"
            )
            assert artifacts_page.get_upload_path_typed_value(
                timeout=UI_ELEMENT_TIMEOUT
            ) == "", (
                "Nothing should be pre-typed in the editable Path segment — the "
                "subfolder must come from the read-only prefix adornment, not "
                "from a pre-filled suffix"
            )

        with allure.step(
            "Step 13 — Verify the modal description names the same upload target"
        ):
            expected_description = (
                f'Files will be uploaded to "{bucket_name}/{SUBFOLDER_KEY}". '
                "Optionally, enter a subfolder path (relative to current "
                "location). Leave empty to upload to the current folder."
            )
            actual_description = artifacts_page.get_upload_path_description_text(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            assert actual_description == expected_description, (
                "The dialog description should name the selected subfolder as "
                f"the upload target.\nExpected: {expected_description!r}\n"
                f"Actual:   {actual_description!r}"
            )

        with allure.step("Step 14 — Click 'Upload'; the upload completes"):
            response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                timeout=NAVIGATION_TIMEOUT,
            )
            assert response.status == 200, (
                f"Upload PUT should return 200, got {response.status} for "
                f"{response.url}"
            )
            # The request URL is the system's own statement of WHERE the object
            # was written — a stronger oracle for "correct subfolder" than the
            # client-rendered listing alone.
            assert f"{bucket_name}/{SUBFOLDER_KEY}{UPLOAD_FILE_NAME}" in response.url, (
                f"The file must be PUT into the '{SUBFOLDER_KEY}' prefix, not the "
                f"bucket root; got {response.url}"
            )

        with allure.step("Step 15 — Verify the success notification is displayed"):
            expect(
                artifacts_page.success_toast_message,
                "The upload success toast should display the exact product string",
            ).to_have_text(SUCCESS_TOAST_TEXT, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"Step 16 — Verify the main panel remains on '{bucket_name} > {SUBFOLDER}'"
        ):
            assert artifacts_page.get_breadcrumb_bucket_text(
                timeout=UI_ELEMENT_TIMEOUT
            ) == bucket_name, "Breadcrumb bucket should be unchanged after the upload"
            assert artifacts_page.get_breadcrumb_folder_names() == [SUBFOLDER], (
                f"The view should stay inside '{SUBFOLDER}' after the upload"
            )
            assert f"folder={SUBFOLDER}" in page.url, (
                f"URL should still carry the folder param after the upload, got {page.url}"
            )
            assert artifacts_page.is_tree_item_selected(
                SUBFOLDER_KEY, timeout=UI_ELEMENT_TIMEOUT
            ), f"Tree node '{SUBFOLDER_KEY}' should still be the selected node"

        with allure.step(
            f"Step 17 — Verify '{UPLOAD_FILE_NAME}' is listed in the file table "
            f"inside subfolder '{SUBFOLDER}'"
        ):
            artifacts_page.wait_for_file_count(2, timeout=TABLE_REFETCH_TIMEOUT)
            file_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert set(file_names) == {UPLOAD_FILE_NAME, SEED_FILE_NAME}, (
                f"Subfolder '{SUBFOLDER}' should hold exactly the seeded file and "
                f"the uploaded one, got {file_names}"
            )

            row_text = artifacts_page.get_file_row_text(
                UPLOAD_FILE_NAME, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert "Text" in row_text, (
                f"The row's Type cell should render 'Text', got: {row_text!r}"
            )
            assert f"{len(UPLOAD_CONTENT)} B" in row_text, (
                f"The row's Size cell should render the uploaded file's size "
                f"({len(UPLOAD_CONTENT)} B), got: {row_text!r}"
            )
            assert LAST_UPDATE_TIMESTAMP_RE.search(row_text), (
                "The row should render a 'Last update' timestamp matching "
                f"'dd-MM-yyyy, hh:mm a', got: {row_text!r}"
            )

            # The left tree is a second, independent rendering of the same
            # placement — a cross-check that the table row is not optimistic.
            assert artifacts_page.is_tree_item_visible(
                f"{SUBFOLDER_KEY}{UPLOAD_FILE_NAME}", timeout=UI_ELEMENT_TIMEOUT
            ), (
                f"The left-panel tree should show '{SUBFOLDER_KEY}{UPLOAD_FILE_NAME}' "
                "under the subfolder"
            )

        with allure.step(
            f"Step 18 — Verify '{UPLOAD_FILE_NAME}' is NOT listed at the root "
            f"level of '{bucket_name}'"
        ):
            artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
            if artifacts_page.get_breadcrumb_folder_names() != []:
                # CLARIFICATION #651 toggle guard again — assert on the root
                # listing only once the view is genuinely back at root.
                logger.info("Still inside a folder after the click — clicking bucket row again")
                artifacts_page.click_bucket_row(bucket_name, timeout=UI_ELEMENT_TIMEOUT)

            assert artifacts_page.get_breadcrumb_folder_names() == [], (
                "The view should be back at the bucket root before the root "
                "listing is asserted"
            )
            artifacts_page.wait_for_file_count(1, timeout=TABLE_REFETCH_TIMEOUT)
            root_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            # Exact equality (not just a `not in` check) also catches a file
            # wrongly written to root under a mangled key.
            assert root_names == [SUBFOLDER], (
                f"The bucket root should contain ONLY the '{SUBFOLDER}' folder row "
                f"— the uploaded file must live in the subfolder; got {root_names}"
            )

        with allure.step(
            "Side-channel check — no console errors across the "
            "select-subfolder → bucket-menu upload → verify flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the bucket-actions upload "
                f"flow: {[m.text for m in console_errors]}"
            )
