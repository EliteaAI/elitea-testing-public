"""UI Tests for ELITEA-1844 / ELITEA-1845 — Delete Flow: delete a single file
via the per-row actions dropdown (confirm) and cancel the confirmation
(file kept intact).

Two sibling test methods, one per case, sharing the same entry point (a file
row's 3-dot actions dropdown -> "Delete" -> the shared delete-confirmation
modal) and diverging at the terminal button:

* **ELITEA-1844** — click "Delete": the file is removed from the table, the
  left-panel tree and S3 storage; pagination drops 4 -> 3; the success toast
  names the file.
* **ELITEA-1845** — click "Cancel": the modal closes, no toast appears, and
  the file row (with its Type/Size/timestamp), the pagination and the storage
  listing are all unchanged.

They are deliberately NOT parameterised into one test (unlike ELITEA-1842/1843,
whose two rows share identical observables): here the terminal actions differ
in KIND, so every assertion would sit behind an `if variant ==` branch. Same
shape as ELITEA-1847 + ELITEA-1846 living side by side in
`test_artifacts_delete_subfolder_checkbox.py`.

Path distinctness (see AFS § Overlap check): this dropdown delete drives RTK's
SINGULAR `deleteArtifact` mutation
(`DELETE /artifacts/artifact/default/{project}/{bucket}?filename=…`), which is
a different endpoint, message and toast from ELITEA-1847's bulk checkbox +
toolbar delete (`/artifacts/artifacts/…?fname[]=…`) and from ELITEA-1856's
file-preview-editor delete.

Case-text drift (reverse-masking guard — assert the LIVE product contract, not
the stale case wording), filed as CLARIFICATION
https://github.com/EliteaAI/elitea-testing-public/issues/1638:

* confirmation message — live `Are you sure to delete the sample.md? It can't
  be restored.` (the case's text drops "the");
* success toast — live `The sample.md file has been successfully deleted.`
  (the case's text says "The artifacts have been deleted successfully", a
  string that exists nowhere in EliteaUI source).

AFS:
    test-specs/artifacts/l2_delete-flow-single-file-actions-dropdown_ELITEA-1844.md
    test-specs/artifacts/l3_delete-flow-single-file-actions-dropdown-cancel_ELITEA-1845.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1 (ELITEA-1844, high) / p2 (ELITEA-1845, medium) — match the case priorities

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_delete_single_file_dropdown.py -v
"""

import logging
from urllib.parse import parse_qs, urlsplit

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # rows, dot-menu, modal elements
NAVIGATION_TIMEOUT = 20_000       # SPA route transition + S3 listing fetch
DELETE_RESPONSE_TIMEOUT = 20_000  # DELETE request + response
TOAST_ABSENCE_TIMEOUT = 3_000     # short poll for a toast expected NOT to appear

FOLDER_1 = "a1"
FOLDER_2 = "folder-a"
FILE_TO_DELETE = "sample.md"
FILE_TO_KEEP = "sample - Copy.md"

FOLDER_1_KEY = f"{FOLDER_1}/file1.txt"
FOLDER_2_KEY = f"{FOLDER_2}/placeholder.txt"

FOLDER_1_CONTENT = b"a1 file\n"
FOLDER_2_CONTENT = b"folder-a file\n"
FILE_TO_KEEP_CONTENT = b"# copy\n"
# Sized to EXACTLY 331 bytes so the row's Size cell reads "331 B", matching the
# cases' own Test Data without depending on any pre-existing environment data.
SAMPLE_MD_CONTENT = ("# ELITEA-1844 sample.md\n\n" + "Delete-flow fixture content line.\n" * 9).encode()

EXPECTED_ROW_TYPE = "Markdown"
EXPECTED_ROW_SIZE = "331 B"

# Live-confirmed text (2026-08-22) — both differ from the cases' own wording;
# CLARIFICATION #1638 filed, reverse-masking guard applied.
EXPECTED_CONFIRM_MESSAGE = "Are you sure to delete the sample.md? It can't be restored."
EXPECTED_SUCCESS_TOAST = "The sample.md file has been successfully deleted."

EXPECTED_MENU_ITEMS = ["Download", "Delete"]
EXPECTED_INITIAL_ITEMS = {FOLDER_1, FOLDER_2, FILE_TO_KEEP, FILE_TO_DELETE}


def _seed_bucket(artifact_api, bucket_name: str) -> None:
    """Seed the 4 top-level items both cases' preconditions describe.

    `ArtifactAPI.upload_file` auto-creates each parent folder node (this is
    S3-key-prefix storage — no separate folder-creation call exists), so two
    nested uploads produce the `a1` and `folder-a` folder rows.
    """
    artifact_api.upload_file(bucket_name, FOLDER_1_KEY, FOLDER_1_CONTENT)
    artifact_api.upload_file(bucket_name, FOLDER_2_KEY, FOLDER_2_CONTENT)
    artifact_api.upload_file(bucket_name, FILE_TO_KEEP, FILE_TO_KEEP_CONTENT)
    artifact_api.upload_file(bucket_name, FILE_TO_DELETE, SAMPLE_MD_CONTENT)


@allure.epic("Artifacts")
@allure.feature("Delete Flow")
class TestArtifactDeleteSingleFileDropdown:
    """ELITEA-1844 — delete a single file via its row actions dropdown."""

    @pytest.mark.p1
    @allure.title(
        "Deleting a single file via the row actions dropdown removes it from "
        "the table, the tree and storage, and updates pagination"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1844_delete-flow-delete-single-file-via-actions-dropdown.md",
        "onetest-ai Test Case link",
    )
    def test_delete_single_file_via_dropdown(self, page, artifact_api, artifact_bucket):
        """Confirming the dropdown's Delete removes exactly that one file.

        The bucket is mutated once at setup (the 4 seeded keys — the minimal
        fresh state a destructive case inherently requires, workflow skill
        Hard Rule 10) and once by the case's own delete; every assertion reads
        that state without further seeding. No substitution of any kind: the
        confirmation text, the toast, the table, the tree and the storage
        listing are all produced by the system under test.
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
            "Steps 1-3 — Navigate to the bucket (folds the case's 'open "
            "Artifacts' + 'click bucket-1'); verify the file table lists all "
            "4 items (a1, folder-a, sample - Copy.md, sample.md)"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            file_names = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert file_names == EXPECTED_INITIAL_ITEMS, (
                f"Expected the 4 seeded top-level items, got {file_names}"
            )

        with allure.step("Step 4 — Verify the pagination reads '1 - 4 of 4'"):
            pagination = artifacts_page.get_pagination_info_text()
            assert pagination == "1 - 4 of 4", (
                f"Expected pagination '1 - 4 of 4', got {pagination!r}"
            )

        with allure.step(
            "Steps 5-6 — Open 'sample.md''s row actions dot-menu; verify it "
            "offers exactly 'Download' and 'Delete'"
        ):
            artifacts_page.open_file_actions_menu(FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT)
            labels = artifacts_page.get_file_actions_menu_item_labels(
                FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert labels == EXPECTED_MENU_ITEMS, (
                f"Expected the dropdown to offer exactly {EXPECTED_MENU_ITEMS}, got {labels}"
            )
            expect(artifacts_page.download_menu_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_menu_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Steps 7-8 — Click 'Delete'; verify the confirmation modal shows "
            "the warning icon, the title 'Delete confirmation', the LIVE "
            "message \"Are you sure to delete the sample.md? It can't be "
            "restored.\" (CLARIFICATION #1638 — the case's text drops 'the'), "
            "the file name in its own emphasised element, the X icon, "
            "'Cancel' and 'Delete'"
        ):
            artifacts_page.click_delete_menu_item(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_title).to_have_text(
                "Delete confirmation", timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.delete_confirm_title_icon).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE, (
                f"Expected the live confirm message {EXPECTED_CONFIRM_MESSAGE!r}, "
                f"got {message_text!r}"
            )
            # The case's "sample.md highlighted in blue": the name is rendered
            # in its own emphasised span (palette.text.deleteAlertEntityName).
            # The COLOUR is not assertable under this project's testid-only
            # locator policy (a computed-style read has no testid handle) —
            # declared in the AFS § Automation Hints; the dedicated element
            # that carries the styling is asserted by text instead.
            expect(artifacts_page.delete_confirm_entity_name).to_have_text(
                FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.delete_confirm_close_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.delete_confirm_cancel_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            expect(artifacts_page.delete_confirm_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 9 — Click 'Delete'; verify exactly one DELETE fires against "
            "the SINGULAR artifact endpoint with filename=sample.md, and "
            "returns 200"
        ):
            response = artifacts_page.confirm_delete_single_artifact(
                timeout=DELETE_RESPONSE_TIMEOUT,
            )
            assert response.status == 200, (
                f"Expected the single-file DELETE to return 200, got {response.status}"
            )
            split = urlsplit(response.url)
            assert "/artifacts/artifact/" in split.path, (
                "Row-dropdown delete must drive the SINGULAR deleteArtifact "
                f"endpoint (/artifacts/artifact/…), got {split.path!r}"
            )
            filename_params = parse_qs(split.query).get("filename", [])
            assert filename_params == [FILE_TO_DELETE], (
                f"Expected DELETE filename param [{FILE_TO_DELETE!r}], got {filename_params}"
            )

        with allure.step(
            "Steps 10-11 — Verify the modal closes and the success toast reads "
            "the LIVE text 'The sample.md file has been successfully deleted.' "
            "(CLARIFICATION #1638)"
        ):
            expect(artifacts_page.delete_confirm_dialog).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.success_toast_message).to_have_text(
                EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Steps 12+14+15 — Verify 'sample.md' is gone from the file table, "
            "the pagination reads '1 - 3 of 3', and the remaining 3 items are "
            "unchanged"
        ):
            # The post-delete refetch is invalidatesTags-driven and settles
            # asynchronously — condition wait, never a bare read.
            artifacts_page.wait_for_file_count(3, timeout=UI_ELEMENT_TIMEOUT)
            names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert names_after == {FOLDER_1, FOLDER_2, FILE_TO_KEEP}, (
                f"Expected exactly the 3 surviving items, got {names_after}"
            )
            pagination_after = artifacts_page.get_pagination_info_text()
            assert pagination_after == "1 - 3 of 3", (
                f"Expected pagination '1 - 3 of 3' after the delete, got {pagination_after!r}"
            )

        with allure.step(
            "Step 13 — Verify the left-panel tree no longer shows 'sample.md', "
            "while its sibling 'sample - Copy.md' is still there (so the "
            "assertion discriminates a removal from a tree that simply failed "
            "to render)"
        ):
            assert not artifacts_page.is_tree_item_visible(FILE_TO_DELETE), (
                f"'{FILE_TO_DELETE}' should no longer be visible in the left-panel tree"
            )
            assert artifacts_page.is_tree_item_visible(FILE_TO_KEEP), (
                f"'{FILE_TO_KEEP}' should still be visible in the left-panel tree"
            )

        with allure.step(
            "Independent ground truth — a raw S3-listing API call (not a "
            "second DOM read) confirms 'sample.md' is gone from storage and "
            "the other 3 keys survive"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert FILE_TO_DELETE not in remaining_keys, (
                f"'{FILE_TO_DELETE}' should be gone from storage, remaining: {remaining_keys}"
            )
            assert {FOLDER_1_KEY, FOLDER_2_KEY, FILE_TO_KEEP} <= remaining_keys, (
                f"The other 3 seeded keys should survive, remaining: {remaining_keys}"
            )

        with allure.step("Side-channel check — no console errors across the flow"):
            assert not console_errors, (
                "Unexpected console errors during the single-file dropdown "
                f"delete flow: {[m.text for m in console_errors]}"
            )


@allure.epic("Artifacts")
@allure.feature("Delete Flow")
class TestArtifactDeleteSingleFileDropdownCancel:
    """ELITEA-1845 — cancelling the delete confirmation keeps the file intact."""

    @pytest.mark.p2
    @allure.title(
        "Cancelling the delete confirmation closes the modal and leaves the "
        "file, its metadata and the pagination unchanged"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1845_delete-flow-delete-single-file-via-actions-dropdown-cancel"
        "-keeps-file-intact.md",
        "onetest-ai Test Case link",
    )
    def test_cancel_delete_keeps_file_intact(self, page, artifact_api, artifact_bucket):
        """Cancel closes the modal and changes nothing.

        Read-only from the bucket's perspective: it is seeded once and the
        case's own action is cancelled, so the final state IS the seeded
        state. Every observable (row text, pagination, toast absence, storage
        listing) is produced by the system under test.
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
            "Steps 1-2 — Navigate to the bucket; verify the 4 seeded items "
            "and the '1 - 4 of 4' pagination, and snapshot 'sample.md''s row "
            "text (Type / Size / timestamp) for the post-cancel comparison"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.wait_for_file_count(4, timeout=NAVIGATION_TIMEOUT)
            names_before = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert names_before == EXPECTED_INITIAL_ITEMS, (
                f"Expected the 4 seeded top-level items, got {names_before}"
            )
            pagination_before = artifacts_page.get_pagination_info_text()
            assert pagination_before == "1 - 4 of 4", (
                f"Expected pagination '1 - 4 of 4', got {pagination_before!r}"
            )
            row_text_before = artifacts_page.get_file_row_text(
                FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert EXPECTED_ROW_TYPE in row_text_before, (
                f"Expected the row to show type {EXPECTED_ROW_TYPE!r}, got {row_text_before!r}"
            )
            assert EXPECTED_ROW_SIZE in row_text_before, (
                f"Expected the row to show size {EXPECTED_ROW_SIZE!r}, got {row_text_before!r}"
            )

        with allure.step(
            "Steps 3-5 — Open 'sample.md''s actions dropdown, click 'Delete', "
            "and verify the confirmation modal shows the LIVE message "
            "(CLARIFICATION #1638)"
        ):
            artifacts_page.open_file_actions_menu(FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT)
            artifacts_page.click_delete_menu_item(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            message_text = artifacts_page.get_delete_confirm_message_text(
                timeout=UI_ELEMENT_TIMEOUT,
            )
            assert message_text == EXPECTED_CONFIRM_MESSAGE, (
                f"Expected the live confirm message {EXPECTED_CONFIRM_MESSAGE!r}, "
                f"got {message_text!r}"
            )

        with allure.step("Steps 6-7 — Click 'Cancel'; verify the modal closes"):
            artifacts_page.click_delete_cancel_button(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.delete_confirm_dialog).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 8 — Verify NO success notification is displayed "
            "(auto-retrying count-0 expectation, correct in both directions)"
        ):
            expect(artifacts_page.success_toast_message).to_have_count(
                0, timeout=TOAST_ABSENCE_TIMEOUT,
            )

        with allure.step(
            "Steps 9-10 — Verify 'sample.md' is still listed with byte-"
            "identical row values (Type / Size / timestamp), the 4 item names "
            "are unchanged and the pagination still reads '1 - 4 of 4'"
        ):
            row_text_after = artifacts_page.get_file_row_text(
                FILE_TO_DELETE, timeout=UI_ELEMENT_TIMEOUT,
            )
            assert row_text_after == row_text_before, (
                "The cancelled delete must leave the row's rendered values "
                f"unchanged: before {row_text_before!r}, after {row_text_after!r}"
            )
            names_after = set(artifacts_page.get_file_names(timeout=UI_ELEMENT_TIMEOUT))
            assert names_after == EXPECTED_INITIAL_ITEMS, (
                f"Expected the same 4 items after cancelling, got {names_after}"
            )
            pagination_after = artifacts_page.get_pagination_info_text()
            assert pagination_after == "1 - 4 of 4", (
                f"Expected pagination to stay '1 - 4 of 4', got {pagination_after!r}"
            )

        with allure.step(
            "Independent ground truth — the S3 listing still contains all 4 "
            "seeded keys, so nothing reached storage"
        ):
            remaining_keys = set(artifact_api.list_bucket_files(bucket_name))
            assert {FOLDER_1_KEY, FOLDER_2_KEY, FILE_TO_KEEP, FILE_TO_DELETE} <= remaining_keys, (
                f"All 4 seeded keys should survive a cancelled delete, got {remaining_keys}"
            )

        with allure.step("Side-channel check — no console errors across the flow"):
            assert not console_errors, (
                "Unexpected console errors during the cancelled-delete flow: "
                f"{[m.text for m in console_errors]}"
            )
