"""UI Test for ELITEA-1847 — Delete Flow: Delete Subfolder via Checkbox
Deletes Folder and Its Contents.

Regression test: verifies that selecting a subfolder row via its checkbox and
confirming the toolbar "Delete selected files" action removes the folder AND
all its underlying files — from the file table, from the left-panel tree, and
(independently) from storage — while every other item in the bucket (a
sibling folder and two root-level files) is left completely unaffected. This
is the FIRST case in this repo to actually exercise ANY artifacts delete flow
— prior automation only ever asserted the per-file dot-menu "Delete" item's
*visibility* (ELITEA-1839's `delete_menu_item`), never clicked it, and never
touched the toolbar bulk-delete icon at all.

Test flow:
1. Seed a fresh bucket (via API) with `a1/file1.txt`, `a1/file2.txt` (the
   subfolder to delete), `folder-a/placeholder.txt` (a sibling folder that
   must survive), and two root-level files `sample.md` / `sample - Copy.md`
   (must also survive).
2. Navigate directly to the bucket; verify all 4 top-level items (`a1`,
   `folder-a`, `sample - Copy.md`, `sample.md`) are listed.
3. Check `a1`'s row checkbox; verify it becomes checked.
4. Verify the toolbar delete icon's tooltip reads "Delete selected files"
   (not "Delete all files" — only 1 of 4 rows is selected).
5. Click the delete icon; verify the "Delete confirmation" modal opens with
   the message "Are you sure to delete the selected files?" — live text,
   CLARIFICATION #659 (case's own text drops "the"; reverse-masking guard —
   assert what the product actually says).
6. Click "Delete"; verify exactly one DELETE request fires whose `fname[]`
   params are `a1`'s fully-expanded underlying file keys (`a1/file1.txt`,
   `a1/file2.txt`) — never a bare `a1/` folder key (confirms
   `expandFoldersToAllItems()`/`getItemsUnderFolder()`'s key-prefix
   expansion, since this S3-backed storage has no server-side folder
   object).
7. Verify the success toast reads "The selected files have been successfully
   deleted." — live text, CLARIFICATION #660 (case's own Test Data wording
   differs; reverse-masking guard).
8. Verify `a1` is gone from the file table (pagination drops to 3 of 3).
9. Verify `a1` is gone from the left-panel tree.
10. Verify — via an INDEPENDENT ground truth beyond the DOM
    (`ArtifactAPI.list_bucket_files()`, a raw S3-listing call, not a second
    DOM read) — that `a1/file1.txt` and `a1/file2.txt` are truly gone from
    storage.
11. Verify the 3 remaining items (`folder-a`, `sample - Copy.md`,
    `sample.md`) are still listed, with the two files' Type/Size unchanged.

Overlap check (see AFS): zero behavioral overlap with any existing artifacts
test — `delete_menu_item` (ELITEA-1839) is visibility-only, never clicked, in
every existing test; no existing test drives the toolbar bulk-delete icon or
a folder-checkbox-driven delete of any kind.

AFS: test-specs/artifacts/l2_delete-flow-subfolder-checkbox-deletes-contents_ELITEA-1847.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_delete_subfolder_checkbox.py -v
"""

import logging
from urllib.parse import parse_qs, urlsplit

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms unless noted)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000    # rows, checkboxes, dialog elements
NAVIGATION_TIMEOUT = 15_000    # SPA route transitions
DELETE_RESPONSE_TIMEOUT = 15_000  # DELETE request + response

FOLDER_TO_DELETE = "a1"
FOLDER_TO_KEEP = "folder-a"
FILE_ROOT_1 = "sample.md"
FILE_ROOT_2 = "sample - Copy.md"

A1_FILE1_KEY = f"{FOLDER_TO_DELETE}/file1.txt"
A1_FILE2_KEY = f"{FOLDER_TO_DELETE}/file2.txt"
FOLDER_A_PLACEHOLDER_KEY = f"{FOLDER_TO_KEEP}/placeholder.txt"

A1_FILE1_CONTENT = b"ELITEA-1847 a1 file1 content\n"
A1_FILE2_CONTENT = b"ELITEA-1847 a1 file2 content\n"
FOLDER_A_PLACEHOLDER_CONTENT = b"ELITEA-1847 folder-a placeholder\n"
SAMPLE_MD_CONTENT = b"# ELITEA-1847 sample.md\n"
SAMPLE_MD_COPY_CONTENT = b"# ELITEA-1847 sample - Copy.md\n"

# Live-confirmed text (implementer + analyst exploration, ELITEA-1847) —
# both deliberately differ from the TMS case's own (stale) wording;
# reverse-masking guard: assert the product's live contract, not the case
# text. CLARIFICATION #659 / #660 filed for the drift.
EXPECTED_CONFIRM_MESSAGE = "Are you sure to delete the selected files?"
EXPECTED_SUCCESS_TOAST = "The selected files have been successfully deleted."


@allure.epic("Artifacts")
@allure.feature("Delete Flow")
class TestArtifactDeleteSubfolderCheckbox:
    """ELITEA-1847 — Delete a subfolder via its row checkbox and the toolbar
    bulk-delete icon; verify the folder and its contents are removed and
    every other bucket item is unaffected.
    """

    @pytest.mark.p1
    @allure.title(
        "Selecting a subfolder via checkbox and confirming toolbar delete "
        "removes the folder and its contents; other items unaffected"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1847_delete-flow-subfolder-checkbox-deletes-contents.md",
        "onetest-ai Test Case link",
    )
    def test_delete_subfolder_via_checkbox(self, page, artifact_api, artifact_bucket):
        """Deleting a subfolder via checkbox removes it and its contents only.

        Bucket is mutated exactly once at setup (seeded with 5 keys — the
        minimal fresh state this observable inherently requires, since the
        case's own purpose is destructive: deleting part of the bucket's
        contents; workflow skill Hard Rule 10) — every assertion afterward
        reads that state (plus the one delete mutation the case itself
        drives) without further seeding.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed all 5 keys via API (ArtifactAPI.upload_file —
        # auto-creates each parent folder node; no separate folder-creation
        # call exists or is needed for this S3-key-prefix-based storage,
        # confirmed live per the AFS). `a1` is the folder to delete;
        # `folder-a` + the two root files must survive untouched.
        # ------------------------------------------------------------------
        artifact_api.upload_file(bucket_name, A1_FILE1_KEY, A1_FILE1_CONTENT)
        artifact_api.upload_file(bucket_name, A1_FILE2_KEY, A1_FILE2_CONTENT)
        artifact_api.upload_file(bucket_name, FOLDER_A_PLACEHOLDER_KEY, FOLDER_A_PLACEHOLDER_CONTENT)
        artifact_api.upload_file(bucket_name, FILE_ROOT_1, SAMPLE_MD_CONTENT)
        artifact_api.upload_file(bucket_name, FILE_ROOT_2, SAMPLE_MD_COPY_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket (folds case steps 1-2: Artifacts "
            "page load + bucket selection); verify the file table shows all "
            "4 top-level items (a1, folder-a, sample - Copy.md, sample.md)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            # `navigate_to_bucket()` now carries the same retry-on-URL-param
            # -loss guard as `navigate_to_bucket_folder()` (issue #638): PR
            # #661's independent re-run showed the ORIGINAL 3/8 exploratory
            # failures were the app silently loading an unrelated bucket, not
            # a standalone S3-listing-fetch lag as first diagnosed — see
            # `navigate_to_bucket()`'s docstring. `wait_for_file_count()` is
            # kept as a real condition-based settle wait for the file table.
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == {
                FOLDER_TO_DELETE, FOLDER_TO_KEEP, FILE_ROOT_1, FILE_ROOT_2,
            }, f"Expected all 4 seeded top-level items, got {file_names}"
            visible_count = artifacts_page.get_file_count(timeout=UI_ELEMENT_TIMEOUT)
            assert visible_count == 4, f"Expected 4 visible rows, got {visible_count}"
            total_count = artifacts_page.get_total_file_count_from_pagination()
            assert total_count == 4, (
                f"Expected pagination to read 4 total items, got {total_count}"
            )

        with allure.step(
            "Step 2 — Click the checkbox next to 'a1'; verify it becomes checked"
        ):
            artifacts_page.select_file_checkbox(FOLDER_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(FOLDER_TO_DELETE), (
                f"'{FOLDER_TO_DELETE}' checkbox should be checked after clicking it"
            )

        with allure.step(
            "Step 3 — Verify the toolbar delete icon's tooltip reads "
            "'Delete selected files' (only 1 of 4 rows selected, not all)"
        ):
            tooltip_text = artifacts_page.get_delete_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == "Delete selected files", (
                f"Expected tooltip 'Delete selected files', got {tooltip_text!r}"
            )

        with allure.step(
            "Step 4 — Click the toolbar delete icon; verify the delete-"
            "confirmation modal opens"
        ):
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 5 — Verify the modal's heading is 'Delete confirmation' and "
            "its message is the LIVE text 'Are you sure to delete the "
            "selected files?' (CLARIFICATION #659 — case's own text drops "
            "'the'; reverse-masking guard: assert the product's live "
            "contract, not the stale case wording)"
        ):
            dialog_text = artifacts_page.delete_confirm_dialog.text_content() or ""
            assert "Delete confirmation" in dialog_text, (
                f"Expected the modal heading 'Delete confirmation' somewhere "
                f"in the dialog's text, got: {dialog_text!r}"
            )
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE, (
                f"Expected live confirm message {EXPECTED_CONFIRM_MESSAGE!r}, "
                f"got {message_text!r}"
            )

        with allure.step(
            "Step 6 — Click 'Delete'; verify exactly one DELETE request "
            "fires whose fname[] params are a1's fully-expanded underlying "
            "file keys (a1/file1.txt, a1/file2.txt) — never a bare 'a1/' "
            "folder key"
        ):
            response = artifacts_page.confirm_delete(timeout=DELETE_RESPONSE_TIMEOUT)
            assert response.status == 200, (
                f"Expected DELETE to return 200, got {response.status}"
            )
            query = parse_qs(urlsplit(response.url).query)
            fname_values = set(query.get("fname[]", []))
            assert fname_values == {A1_FILE1_KEY, A1_FILE2_KEY}, (
                f"Expected DELETE fname[] params to be exactly the folder's "
                f"expanded file keys {{{A1_FILE1_KEY!r}, {A1_FILE2_KEY!r}}}, "
                f"got {fname_values}"
            )

        with allure.step(
            "Step 7 — Verify the success toast shows the LIVE text 'The "
            "selected files have been successfully deleted.' (CLARIFICATION "
            "#660 — case's own Test Data wording differs; reverse-masking "
            "guard applies the same way as Step 5)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 8 — Verify 'a1' is no longer listed in the file table; "
            "pagination now reads 3 total items"
        ):
            # Same condition-based settle as Step 1 — the post-delete
            # refetch (invalidatesTags-driven, per the AFS's Network
            # Behavior section) races the same way against a bare read.
            artifacts_page.wait_for_file_count(3, timeout=UI_ELEMENT_TIMEOUT)
            file_names_after = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert FOLDER_TO_DELETE not in file_names_after, (
                f"'{FOLDER_TO_DELETE}' should no longer be listed, got: "
                f"{file_names_after}"
            )
            total_after = artifacts_page.get_total_file_count_from_pagination()
            assert total_after == 3, (
                f"Expected pagination to read 3 total items after delete, "
                f"got {total_after}"
            )

        with allure.step(
            "Step 9 — Verify 'a1' is no longer shown in the left-panel tree"
        ):
            assert not artifacts_page.is_tree_item_visible(f"{FOLDER_TO_DELETE}/"), (
                f"'{FOLDER_TO_DELETE}/' should no longer be visible in the "
                f"left-panel tree"
            )

        with allure.step(
            "Step 10 — Verify, via an INDEPENDENT ground truth beyond the "
            "DOM (a raw S3-listing API call, not a second DOM read), that "
            "a1/file1.txt and a1/file2.txt are truly gone from storage"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert A1_FILE1_KEY not in remaining_keys, (
                f"'{A1_FILE1_KEY}' should be gone from storage, remaining "
                f"keys: {remaining_keys}"
            )
            assert A1_FILE2_KEY not in remaining_keys, (
                f"'{A1_FILE2_KEY}' should be gone from storage, remaining "
                f"keys: {remaining_keys}"
            )
            assert remaining_keys == {
                FOLDER_A_PLACEHOLDER_KEY, FILE_ROOT_1, FILE_ROOT_2,
            }, (
                f"Expected exactly the 3 surviving keys after delete, got "
                f"{remaining_keys}"
            )

        with allure.step(
            "Step 11 — Verify the 3 remaining items (folder-a, "
            "sample - Copy.md, sample.md) are still listed, with the two "
            "files' Type/Size cells unchanged from Step 1's baseline"
        ):
            final_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert final_names == {FOLDER_TO_KEEP, FILE_ROOT_1, FILE_ROOT_2}, (
                f"Expected exactly the 3 surviving items, got {final_names}"
            )

            sample_md_row = artifacts_page.get_file_row_text(
                FILE_ROOT_1, timeout=UI_ELEMENT_TIMEOUT
            )
            assert "Markdown" in sample_md_row, (
                f"'{FILE_ROOT_1}' row should show Type 'Markdown', row text "
                f"was: {sample_md_row!r}"
            )
            expected_sample_md_size = f"{len(SAMPLE_MD_CONTENT)} B"
            assert expected_sample_md_size in sample_md_row, (
                f"'{FILE_ROOT_1}' row should show Size "
                f"{expected_sample_md_size!r}, row text was: {sample_md_row!r}"
            )

            sample_md_copy_row = artifacts_page.get_file_row_text(
                FILE_ROOT_2, timeout=UI_ELEMENT_TIMEOUT
            )
            assert "Markdown" in sample_md_copy_row, (
                f"'{FILE_ROOT_2}' row should show Type 'Markdown', row text "
                f"was: {sample_md_copy_row!r}"
            )
            expected_sample_md_copy_size = f"{len(SAMPLE_MD_COPY_CONTENT)} B"
            assert expected_sample_md_copy_size in sample_md_copy_row, (
                f"'{FILE_ROOT_2}' row should show Size "
                f"{expected_sample_md_copy_size!r}, row text was: "
                f"{sample_md_copy_row!r}"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole delete flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the subfolder-delete flow: "
                f"{[m.text for m in console_errors]}"
            )

    FOLDER_KEEP_1 = "a1"
    FOLDER_KEEP_2 = "folder-a"
    FILE_DELETE_1 = "sample - Copy.md"
    FILE_DELETE_2 = "sample.md"

    A1_FILE1_KEY = f"{FOLDER_KEEP_1}/file1.txt"
    FOLDER_A_PLACEHOLDER_KEY = f"{FOLDER_KEEP_2}/placeholder.txt"

    A1_FILE1_CONTENT = b"ELITEA-1846 a1 file1 content\n"
    FOLDER_A_PLACEHOLDER_CONTENT = b"ELITEA-1846 folder-a placeholder\n"
    SAMPLE_MD_CONTENT = b"# ELITEA-1846 sample.md\n"
    SAMPLE_MD_COPY_CONTENT = b"# ELITEA-1846 sample - Copy.md\n"

    # Live-confirmed text, same shared-component CLARIFICATIONs ELITEA-1847
    # already documents (#659 confirm message, #660 success toast) —
    # re-confirmed live this run to apply identically to this case's own
    # 2-file selection flow.
    EXPECTED_CONFIRM_MESSAGE = "Are you sure to delete the selected files?"
    EXPECTED_SUCCESS_TOAST = "The selected files have been successfully deleted."

    @pytest.mark.p2
    @allure.title(
        "Selecting 2 individual files via checkbox (partial selection) drives "
        "the header checkbox indeterminate and deletes only those files"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1846_delete-flow-multiple-files-partial-selection.md",
        "onetest-ai Test Case link",
    )
    def test_delete_multiple_files_partial_selection(self, page, artifact_api, artifact_bucket):
        """Checking 2 file checkboxes (partial selection) drives the header
        'select all' checkbox into the INDETERMINATE state, leaves sibling
        folder checkboxes unchecked, and deleting via the toolbar removes
        only the 2 selected files — subfolders completely unaffected.

        Own fresh `artifact_bucket` instance (function-scoped fixture) —
        deliberately NOT sharing state with `test_delete_subfolder_via_checkbox`
        above, since that test's own core assertion (a1 gets deleted) directly
        conflicts with this test's own precondition (a1 must survive).
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifact_api.upload_file(bucket_name, self.A1_FILE1_KEY, self.A1_FILE1_CONTENT)
        artifact_api.upload_file(bucket_name, self.FOLDER_A_PLACEHOLDER_KEY, self.FOLDER_A_PLACEHOLDER_CONTENT)
        artifact_api.upload_file(bucket_name, self.FILE_DELETE_2, self.SAMPLE_MD_CONTENT)
        artifact_api.upload_file(bucket_name, self.FILE_DELETE_1, self.SAMPLE_MD_COPY_CONTENT)

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket; verify all 4 top-level items "
            "(a1, folder-a, sample - Copy.md, sample.md) are listed"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == {
                self.FOLDER_KEEP_1, self.FOLDER_KEEP_2, self.FILE_DELETE_1, self.FILE_DELETE_2,
            }, f"Expected all 4 seeded top-level items, got {file_names}"
            assert artifacts_page.get_total_file_count_from_pagination() == 4

        with allure.step(
            "Step 2 — Click the checkbox for 'sample - Copy.md'; verify it "
            "becomes checked"
        ):
            artifacts_page.select_file_checkbox(self.FILE_DELETE_1, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(self.FILE_DELETE_1)

        with allure.step(
            "Step 3 — Click the checkbox for 'sample.md'; verify it becomes checked"
        ):
            artifacts_page.select_file_checkbox(self.FILE_DELETE_2, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_checkbox_checked(self.FILE_DELETE_2)

        with allure.step(
            "Step 4 — Verify subfolders 'a1' and 'folder-a' remain unchecked "
            "(query every visible row independently)"
        ):
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == {
                self.FOLDER_KEEP_1: False,
                self.FOLDER_KEEP_2: False,
                self.FILE_DELETE_1: True,
                self.FILE_DELETE_2: True,
            }, f"Unexpected checkbox states: {states}"

        with allure.step(
            "Step 5 — Verify the header 'select all' checkbox shows the "
            "INDETERMINATE state (2 of 4 rows selected — neither fully "
            "checked nor fully unchecked)"
        ):
            assert artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should be indeterminate with a partial selection"
            assert not artifacts_page.is_select_all_checkbox_checked(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should NOT be fully checked with a partial selection"

        with allure.step(
            "Step 6 — Verify the toolbar delete icon's tooltip reads "
            "'Delete selected files' (2 of 4 rows selected, not all)"
        ):
            tooltip_text = artifacts_page.get_delete_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == "Delete selected files", (
                f"Expected tooltip 'Delete selected files', got {tooltip_text!r}"
            )

        with allure.step(
            "Step 7 — Click the toolbar delete icon; verify the delete-"
            "confirmation modal opens"
        ):
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 8 — Verify the modal's heading is 'Delete confirmation' and "
            "its message is the LIVE text 'Are you sure to delete the "
            "selected files?' (CLARIFICATION #659, already filed by "
            "ELITEA-1847 for this shared component; reverse-masking guard: "
            "assert the product's live contract, not the stale case wording)"
        ):
            dialog_text = artifacts_page.delete_confirm_dialog.text_content() or ""
            assert "Delete confirmation" in dialog_text
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == self.EXPECTED_CONFIRM_MESSAGE, (
                f"Expected live confirm message {self.EXPECTED_CONFIRM_MESSAGE!r}, "
                f"got {message_text!r}"
            )

        with allure.step(
            "Step 9 — Click 'Delete'; verify exactly one DELETE request "
            "fires whose fname[] params are the 2 literal selected file "
            "keys (not a folder-expanded list)"
        ):
            response = artifacts_page.confirm_delete(timeout=DELETE_RESPONSE_TIMEOUT)
            assert response.status == 200
            query = parse_qs(urlsplit(response.url).query)
            fname_values = set(query.get("fname[]", []))
            assert fname_values == {self.FILE_DELETE_1, self.FILE_DELETE_2}, (
                f"Expected DELETE fname[] params to be exactly "
                f"{{{self.FILE_DELETE_1!r}, {self.FILE_DELETE_2!r}}}, got {fname_values}"
            )

        with allure.step("Step 10 — Verify the modal closes"):
            expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 11 — Verify the success toast shows the LIVE text 'The "
            "selected files have been successfully deleted.' "
            "(CLARIFICATION #660, already filed by ELITEA-1847 for this "
            "shared component)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                self.EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 12 — Verify 'sample - Copy.md' and 'sample.md' are no "
            "longer listed; only a1/folder-a remain"
        ):
            artifacts_page.wait_for_file_count(2, timeout=UI_ELEMENT_TIMEOUT)
            file_names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names_after == {self.FOLDER_KEEP_1, self.FOLDER_KEEP_2}, (
                f"Expected only a1/folder-a to remain, got {file_names_after}"
            )

        with allure.step(
            "Step 13 — Verify 'sample - Copy.md' and 'sample.md' are no "
            "longer shown in the left-panel tree"
        ):
            assert not artifacts_page.is_tree_item_visible(
                self.FILE_DELETE_1, timeout=UI_ELEMENT_TIMEOUT
            )
            assert not artifacts_page.is_tree_item_visible(
                self.FILE_DELETE_2, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 14 — Verify, via an INDEPENDENT ground truth beyond the "
            "DOM, that a1/folder-a and their own underlying files are "
            "completely unaffected"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert remaining_keys == {
                self.A1_FILE1_KEY, self.FOLDER_A_PLACEHOLDER_KEY,
            }, f"Expected exactly the 2 surviving keys, got {remaining_keys}"

        with allure.step(
            "Step 15 — Verify pagination updates to '1 - 2 of 2'"
        ):
            assert artifacts_page.get_total_file_count_from_pagination() == 2

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "multi-file partial-selection delete flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the multi-file delete flow: "
                f"{[m.text for m in console_errors]}"
            )
