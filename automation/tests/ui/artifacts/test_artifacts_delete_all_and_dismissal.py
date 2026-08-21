"""UI Tests for ELITEA-1848 / ELITEA-1849 / ELITEA-1850 — Delete Flow:
delete-all via the header "Select all" checkbox, and the two modal-dismissal
paths (Cancel and the header X) that must change nothing.

Three sibling regression tests over ONE flow (select rows -> toolbar delete
icon -> shared DeleteEntityModal), split by terminal action:

* ELITEA-1848 — "Select all" + "Delete all files" icon + Delete: every file
  AND folder is removed, the bucket itself survives, and both panels fall
  back to their empty state.
* ELITEA-1849 — the same full selection, then Cancel: nothing is deleted, no
  notification appears, and the selection is retained.
* ELITEA-1850 — a PARTIAL selection (2 of 4 rows, so the "selected files"
  branch is exercised, not "all files"), then the modal's X: same
  no-op outcome, with every previously checked row still checked.

They are three test methods rather than a parameterized family because the
terminal actions differ in KIND, not in parameter value — 1848 asserts
deletion, 1849/1850 assert non-deletion — the same shape ELITEA-1847 +
ELITEA-1846 use in test_artifacts_delete_subfolder_checkbox.py.

Overlap check (see AFS): no existing artifacts test ever clicks the header
`artifacts-select-all-checkbox` (both existing bulk-delete tests use partial
selections and assert the "Delete selected files" branch), and none clicks
the delete modal's X on any path — ELITEA-1844 only asserted that X's
presence.

Live-verified case-text drifts, handled by the reverse-masking guard (assert
the product's contract, not the stale case text):
* the all-selected confirmation reads "Are you sure to delete the all files?"
  — CLARIFICATION #1640 (sibling of #659; the live string is also
  ungrammatical, flagged there for a product-copy call);
* the bulk success toast reads "The selected files have been successfully
  deleted." for BOTH partial and full selections — the exact drift #660
  already tracks (commented there, not re-filed).

AFS:
    test-specs/artifacts/l2_delete-flow-delete-all-select-all-checkbox_ELITEA-1848.md
    test-specs/artifacts/l3_delete-flow-cancel-delete-all-keeps-items_ELITEA-1849.md
    test-specs/artifacts/l3_delete-flow-close-x-on-delete-confirmation_ELITEA-1850.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1 (ELITEA-1848, case priority high) / p2 (ELITEA-1849, ELITEA-1850,
      case priority medium)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_delete_all_and_dismissal.py -v
"""

import logging
from urllib.parse import parse_qs, urlsplit

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, checkboxes, dialog elements
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions
DELETE_RESPONSE_TIMEOUT = 20_000  # DELETE request + response
# Window a toast is WAITED FOR before its absence may be concluded. The
# positive control is `test_delete_all_files_via_select_all` in this same
# file: it sees the same `toast-message` locator carry text immediately after
# the DELETE response, so the detector is proven. `to_have_count(0)` would be
# true at its first poll and could not see a toast rendering 300 ms later
# (reviewer finding on ELITEA-1845).
TOAST_ABSENCE_WINDOW = 3_000

FOLDER_1 = "a1"
FOLDER_2 = "folder-a"
FILE_1 = "sample.md"
FILE_2 = "sample - Copy.md"
ALL_ITEMS = {FOLDER_1, FOLDER_2, FILE_1, FILE_2}

FOLDER_1_KEY = f"{FOLDER_1}/file1.txt"
FOLDER_2_KEY = f"{FOLDER_2}/placeholder.txt"
ALL_KEYS = {FOLDER_1_KEY, FOLDER_2_KEY, FILE_1, FILE_2}

FOLDER_1_CONTENT = b"ELITEA-1848 a1 file1 content\n"
FOLDER_2_CONTENT = b"ELITEA-1848 folder-a placeholder\n"
FILE_1_CONTENT = b"# ELITEA-1848 sample.md\n"
FILE_2_CONTENT = b"# ELITEA-1848 sample - Copy.md\n"

# Live-confirmed strings (2026-08-22). Deliberately NOT the case text — see
# the module docstring's drift note.
EXPECTED_MODAL_TITLE = "Delete confirmation"
EXPECTED_CONFIRM_MESSAGE_ALL = "Are you sure to delete the all files?"
EXPECTED_CONFIRM_MESSAGE_SELECTED = "Are you sure to delete the selected files?"
EXPECTED_ENTITY_NAME_ALL = "all files"
EXPECTED_ENTITY_NAME_SELECTED = "selected files"
EXPECTED_SUCCESS_TOAST = "The selected files have been successfully deleted."
EXPECTED_TOOLTIP_ALL = "Delete all files"
EXPECTED_TOOLTIP_SELECTED = "Delete selected files"
EXPECTED_EMPTY_STATE_TEXT = "No files in this bucket"
EXPECTED_PAGINATION = "1 - 4 of 4"


def _seed_bucket(artifact_api, bucket_name: str) -> None:
    """Seed the 4 top-level items every case in this file starts from.

    Two folders (each with one underlying file — this S3-key-prefix storage
    has no folder objects) and two root-level files.
    """
    artifact_api.upload_file(bucket_name, FOLDER_1_KEY, FOLDER_1_CONTENT)
    artifact_api.upload_file(bucket_name, FOLDER_2_KEY, FOLDER_2_CONTENT)
    artifact_api.upload_file(bucket_name, FILE_1, FILE_1_CONTENT)
    artifact_api.upload_file(bucket_name, FILE_2, FILE_2_CONTENT)


@allure.epic("Artifacts")
@allure.feature("Delete Flow")
class TestArtifactDeleteAllAndDismissal:
    """Delete-all via the select-all checkbox, plus the Cancel and X
    dismissal paths of the shared delete-confirmation modal.
    """

    @pytest.mark.p1
    @allure.title(
        "Select all + 'Delete all files' deletes every file and folder, "
        "leaving the bucket itself with an empty state in both panels"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1848_delete-flow-delete-all-select-all-checkbox.md",
        "onetest-ai Test Case link",
    )
    def test_delete_all_files_via_select_all(self, page, artifact_api, artifact_bucket):
        """Deleting a full selection empties the bucket without deleting it.

        Bucket is mutated exactly once at setup (4 seeded keys — the minimal
        fresh state this observable inherently requires, since the case's own
        purpose is destructive), then only by the delete the case itself
        drives. Own `artifact_bucket` instance: this test empties its bucket,
        which directly contradicts the two dismissal tests' preconditions.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        _seed_bucket(artifact_api, bucket_name)
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket (folds case steps 1-2: Artifacts "
            "page load + bucket selection); verify the file table lists all 4 "
            "items (a1, folder-a, sample - Copy.md, sample.md)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == ALL_ITEMS, (
                f"Expected all 4 seeded top-level items, got {file_names}"
            )
            assert artifacts_page.get_pagination_info_text() == EXPECTED_PAGINATION, (
                "Expected pagination "
                f"{EXPECTED_PAGINATION!r}, got "
                f"{artifacts_page.get_pagination_info_text()!r}"
            )

        with allure.step(
            "Step 2 — Click the header 'Select all' checkbox; verify all 4 "
            "rows become checked (both subfolders and both files)"
        ):
            artifacts_page.click_select_all_checkbox(timeout=UI_ELEMENT_TIMEOUT)
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == {name: True for name in ALL_ITEMS}, (
                f"Expected every row checked after 'Select all', got {states}"
            )

        with allure.step(
            "Step 3 — Verify the header checkbox shows the fully-checked "
            "state (checked, and NOT indeterminate)"
        ):
            assert artifacts_page.is_select_all_checkbox_checked(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should be fully checked with every row selected"
            assert not artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should NOT be indeterminate with every row selected"

        with allure.step(
            "Step 4 — Verify the toolbar delete icon's tooltip reads 'Delete "
            "all files' (the all-selected branch, not 'Delete selected files')"
        ):
            tooltip_text = artifacts_page.get_delete_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == EXPECTED_TOOLTIP_ALL, (
                f"Expected tooltip {EXPECTED_TOOLTIP_ALL!r}, got {tooltip_text!r}"
            )

        with allure.step(
            "Step 5 — Click the 'Delete all files' icon; verify the "
            "delete-confirmation modal opens"
        ):
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 6 — Verify the modal's parts: warning icon, title 'Delete "
            "confirmation', the LIVE message 'Are you sure to delete the all "
            "files?' with 'all files' as the emphasised (blue) span, plus the "
            "X, 'Cancel' and 'Delete' controls (CLARIFICATION #1640 — the "
            "case's own wording drops 'the'; reverse-masking guard: assert "
            "the product's live contract)"
        ):
            expect(artifacts_page.delete_confirm_title_icon).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.delete_confirm_title).to_have_text(
                EXPECTED_MODAL_TITLE, timeout=UI_ELEMENT_TIMEOUT
            )
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE_ALL, (
                f"Expected live confirm message {EXPECTED_CONFIRM_MESSAGE_ALL!r}, "
                f"got {message_text!r}"
            )
            expect(artifacts_page.delete_confirm_entity_name).to_have_text(
                EXPECTED_ENTITY_NAME_ALL, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.delete_confirm_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.delete_confirm_cancel_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.delete_confirm_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 7 — Click 'Delete'; verify exactly one DELETE request fires "
            "whose fname[] params are the 4 FULLY-EXPANDED storage keys "
            "(folders expanded to their underlying files — never a bare 'a1/')"
        ):
            response = artifacts_page.confirm_delete(timeout=DELETE_RESPONSE_TIMEOUT)
            assert response.status == 200, (
                f"Expected DELETE to return 200, got {response.status}"
            )
            query = parse_qs(urlsplit(response.url).query)
            fname_values = set(query.get("fname[]", []))
            assert fname_values == ALL_KEYS, (
                f"Expected DELETE fname[] params to be exactly the expanded "
                f"keys {ALL_KEYS}, got {fname_values}"
            )

        with allure.step("Step 8 — Verify the modal closes"):
            expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 9 — Verify the success notification shows the LIVE text "
            "'The selected files have been successfully deleted.' (the bulk "
            "toast is NOT branched on all-vs-partial; the case's own wording "
            "is the drift #660 already tracks)"
        ):
            expect(artifacts_page.success_toast_message).to_have_text(
                EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 10 — Verify the file table is empty — no files and no "
            "subfolders are listed"
        ):
            artifacts_page.wait_for_file_count(0, timeout=NAVIGATION_TIMEOUT)
            remaining_names = artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT)
            assert remaining_names == [], (
                f"Expected an empty file table, got {remaining_names}"
            )

        with allure.step(
            "Step 11 — Verify the main panel shows the empty state "
            "('No files in this bucket')"
        ):
            assert artifacts_page.is_bucket_empty(timeout=UI_ELEMENT_TIMEOUT), (
                "Main panel should show the empty state after deleting every item"
            )
            expect(artifacts_page.empty_state_label).to_have_text(
                EXPECTED_EMPTY_STATE_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 12 — Verify the left-panel tree shows 'No files in this "
            "bucket' under the bucket"
        ):
            expect(artifacts_page.bucket_tree_empty_label(bucket_name)).to_have_text(
                EXPECTED_EMPTY_STATE_TEXT, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 13 — Verify the bucket itself still exists in the bucket "
            "list (emptying a bucket does not delete it)"
        ):
            artifacts_page.wait_for_bucket_in_list(bucket_name, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 14 (beyond the case) — Verify via an INDEPENDENT ground "
            "truth beyond the DOM (a raw S3-listing API call, not a second "
            "DOM read) that the bucket holds no keys at all"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert remaining_keys == set(), (
                f"Expected zero keys left in storage, got {remaining_keys}"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "delete-all flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the delete-all flow: "
                f"{[m.text for m in console_errors]}"
            )

    @pytest.mark.p2
    @allure.title(
        "Cancel on the 'Delete all files' confirmation deletes nothing, "
        "shows no notification and keeps every item selected"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1849_delete-flow-cancel-delete-all-keeps-items.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_delete_all_keeps_items_intact(self, page, artifact_api, artifact_bucket):
        """Cancelling the delete-all modal is a complete no-op.

        Own fresh `artifact_bucket` instance — deliberately NOT sharing state
        with the delete-all test above, whose own core assertion (the bucket
        ends empty) contradicts this test's precondition.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        delete_requests = []
        page.on(
            "request",
            lambda req: delete_requests.append(req.url) if req.method == "DELETE" else None,
        )

        _seed_bucket(artifact_api, bucket_name)
        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to the bucket (folds case steps 1-2); verify "
            "all 4 items are listed and snapshot each row's text for the "
            "byte-for-byte post-cancel comparison"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == ALL_ITEMS, (
                f"Expected all 4 seeded top-level items, got {file_names}"
            )
            assert artifacts_page.get_pagination_info_text() == EXPECTED_PAGINATION
            rows_before = {
                name: artifacts_page.get_file_row_text(name, timeout=UI_ELEMENT_TIMEOUT)
                for name in sorted(ALL_ITEMS)
            }

        with allure.step(
            "Step 2 — Click the header 'Select all' checkbox; verify all 4 "
            "items are selected"
        ):
            artifacts_page.click_select_all_checkbox(timeout=UI_ELEMENT_TIMEOUT)
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == {name: True for name in ALL_ITEMS}, (
                f"Expected every row checked after 'Select all', got {states}"
            )
            assert artifacts_page.is_select_all_checkbox_checked(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should be fully checked with every row selected"

        with allure.step(
            "Step 3 — Click the 'Delete all files' icon; verify the modal "
            "opens with the LIVE message 'Are you sure to delete the all "
            "files?' (CLARIFICATION #1640)"
        ):
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE_ALL, (
                f"Expected live confirm message {EXPECTED_CONFIRM_MESSAGE_ALL!r}, "
                f"got {message_text!r}"
            )

        with allure.step("Step 4 — Click 'Cancel'; verify the modal closes"):
            artifacts_page.click_delete_cancel_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 5 — Verify NO success notification is displayed: wait a "
            "full toast window for 'toast-message' to appear and require the "
            "wait to time out (the detector is proven by the delete-all test "
            "in this same file, which sees this locator carry text after a "
            "real delete)"
        ):
            with pytest.raises(PlaywrightTimeoutError):
                artifacts_page.success_toast_message.wait_for(
                    state="visible", timeout=TOAST_ABSENCE_WINDOW
                )

        with allure.step(
            "Step 6 — Verify all 4 items remain in the file table unchanged "
            "(names, per-row text byte-for-byte) and pagination still reads "
            "'1 - 4 of 4'"
        ):
            file_names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names_after == ALL_ITEMS, (
                f"Expected all 4 items still listed after Cancel, got {file_names_after}"
            )
            rows_after = {
                name: artifacts_page.get_file_row_text(name, timeout=UI_ELEMENT_TIMEOUT)
                for name in sorted(ALL_ITEMS)
            }
            assert rows_after == rows_before, (
                "Row text changed after Cancel — expected byte-for-byte "
                f"identical rows.\nBefore: {rows_before}\nAfter:  {rows_after}"
            )
            assert artifacts_page.get_pagination_info_text() == EXPECTED_PAGINATION, (
                "Pagination changed after Cancel — expected "
                f"{EXPECTED_PAGINATION!r}, got "
                f"{artifacts_page.get_pagination_info_text()!r}"
            )

        with allure.step(
            "Step 7 — Verify the left-panel tree under the bucket is "
            "unchanged (both folders and both files still shown)"
        ):
            for item_key in (f"{FOLDER_1}/", f"{FOLDER_2}/", FILE_1, FILE_2):
                assert artifacts_page.is_tree_item_visible(
                    item_key, timeout=UI_ELEMENT_TIMEOUT
                ), f"Tree item {item_key!r} should still be visible after Cancel"

        with allure.step(
            "Step 8 (beyond the case) — Verify no DELETE request was made at "
            "all, the selection is retained, and an INDEPENDENT S3 listing "
            "still returns all 4 seeded keys"
        ):
            assert delete_requests == [], (
                f"Cancel must fire no DELETE request, captured: {delete_requests}"
            )
            states_after = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states_after == {name: True for name in ALL_ITEMS}, (
                f"Selection should survive Cancel, got {states_after}"
            )
            assert artifacts_page.is_select_all_checkbox_checked(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should still be fully checked after Cancel"
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert remaining_keys == ALL_KEYS, (
                f"Expected all 4 seeded keys still in storage, got {remaining_keys}"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "cancel-delete-all flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the cancel-delete-all flow: "
                f"{[m.text for m in console_errors]}"
            )

    @pytest.mark.p2
    @allure.title(
        "Closing the delete-confirmation modal with X deletes nothing and "
        "leaves the previously selected items still checked"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1850_delete-flow-close-x-on-delete-confirmation.md",
        "onetest-ai Test Case link",
    )
    def test_close_x_on_delete_confirmation_keeps_items_intact(
        self, page, artifact_api, artifact_bucket
    ):
        """Dismissing the delete modal with X is a no-op that preserves the
        selection.

        The case says "select one or more items" and names the "Delete
        selected files" icon — so 2 of 4 rows are selected deliberately: a
        full selection would silently move this case onto the "all files"
        branch (ELITEA-1848's) and lose the "selected files" coverage. Own
        fresh `artifact_bucket` instance.
        """
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        delete_requests = []
        page.on(
            "request",
            lambda req: delete_requests.append(req.url) if req.method == "DELETE" else None,
        )

        _seed_bucket(artifact_api, bucket_name)
        artifacts_page = ArtifactsPage(page)
        expected_selection = {
            FOLDER_1: False, FOLDER_2: False, FILE_1: True, FILE_2: True,
        }

        with allure.step(
            "Step 1 — Navigate to the bucket (folds case steps 1-2); verify "
            "all 4 items are listed and snapshot each row's text"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == ALL_ITEMS, (
                f"Expected all 4 seeded top-level items, got {file_names}"
            )
            assert artifacts_page.get_pagination_info_text() == EXPECTED_PAGINATION
            rows_before = {
                name: artifacts_page.get_file_row_text(name, timeout=UI_ELEMENT_TIMEOUT)
                for name in sorted(ALL_ITEMS)
            }

        with allure.step(
            "Step 2 — Select 2 of the 4 items (sample.md, sample - Copy.md) "
            "via their row checkboxes; verify exactly those two are checked "
            "and the header checkbox goes indeterminate"
        ):
            artifacts_page.select_file_checkbox(FILE_1, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.select_file_checkbox(FILE_2, timeout=UI_ELEMENT_TIMEOUT)
            states = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states == expected_selection, (
                f"Expected only the two files checked, got {states}"
            )
            assert artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should be indeterminate with a partial selection"

        with allure.step(
            "Step 3 — Verify the toolbar icon's tooltip reads 'Delete "
            "selected files' (the partial-selection branch the case names), "
            "click it, and verify the modal opens with the matching message "
            "and emphasised entity name"
        ):
            tooltip_text = artifacts_page.get_delete_button_tooltip_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert tooltip_text == EXPECTED_TOOLTIP_SELECTED, (
                f"Expected tooltip {EXPECTED_TOOLTIP_SELECTED!r}, got {tooltip_text!r}"
            )
            artifacts_page.click_delete_files_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.delete_confirm_title).to_have_text(
                EXPECTED_MODAL_TITLE, timeout=UI_ELEMENT_TIMEOUT
            )
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE_SELECTED, (
                f"Expected live confirm message "
                f"{EXPECTED_CONFIRM_MESSAGE_SELECTED!r}, got {message_text!r}"
            )
            expect(artifacts_page.delete_confirm_entity_name).to_have_text(
                EXPECTED_ENTITY_NAME_SELECTED, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Click the X (close) icon in the modal's top-right "
            "corner; verify the modal closes"
        ):
            artifacts_page.click_delete_close_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 5 — Verify NO success notification is displayed: wait a "
            "full toast window for 'toast-message' to appear and require the "
            "wait to time out (detector proven by the delete-all test in this "
            "same file)"
        ):
            with pytest.raises(PlaywrightTimeoutError):
                artifacts_page.success_toast_message.wait_for(
                    state="visible", timeout=TOAST_ABSENCE_WINDOW
                )

        with allure.step(
            "Step 6 — Verify every item remains in the file table unchanged "
            "AND the previously selected files are STILL CHECKED (header "
            "still indeterminate, pagination still '1 - 4 of 4')"
        ):
            file_names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names_after == ALL_ITEMS, (
                f"Expected all 4 items still listed after X, got {file_names_after}"
            )
            rows_after = {
                name: artifacts_page.get_file_row_text(name, timeout=UI_ELEMENT_TIMEOUT)
                for name in sorted(ALL_ITEMS)
            }
            assert rows_after == rows_before, (
                "Row text changed after closing the modal with X — expected "
                f"byte-for-byte identical rows.\nBefore: {rows_before}\n"
                f"After:  {rows_after}"
            )
            states_after = artifacts_page.get_checkbox_states(timeout=UI_ELEMENT_TIMEOUT)
            assert states_after == expected_selection, (
                f"Selection should survive the X dismissal, got {states_after}"
            )
            assert artifacts_page.is_select_all_checkbox_indeterminate(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Header checkbox should still be indeterminate after the X dismissal"
            assert artifacts_page.get_pagination_info_text() == EXPECTED_PAGINATION, (
                "Pagination changed after the X dismissal — expected "
                f"{EXPECTED_PAGINATION!r}, got "
                f"{artifacts_page.get_pagination_info_text()!r}"
            )

        with allure.step(
            "Step 7 (beyond the case) — Verify no DELETE request was made at "
            "all and an INDEPENDENT S3 listing still returns all 4 seeded keys"
        ):
            assert delete_requests == [], (
                f"Closing with X must fire no DELETE request, captured: {delete_requests}"
            )
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert remaining_keys == ALL_KEYS, (
                f"Expected all 4 seeded keys still in storage, got {remaining_keys}"
            )

        with allure.step(
            "Side-channel check — no console errors across the whole "
            "close-with-X flow"
        ):
            assert not console_errors, (
                "Unexpected console errors during the close-with-X flow: "
                f"{[m.text for m in console_errors]}"
            )
