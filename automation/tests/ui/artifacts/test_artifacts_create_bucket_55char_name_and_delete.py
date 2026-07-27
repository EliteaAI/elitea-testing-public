"""UI Test for ELITEA-1817 — Create Artifact Bucket with a 56-Character Name
and Delete It via the Actions Menu.

Regression test: verifies a bucket name at the exact max-length boundary
(``CreateBucket.jsx``'s yup schema: ``.max(56, ...)``) is accepted with no
character-limit warning, then drives the FIRST-ever bucket-level delete via
the bucket-row dot-menu's "Delete" entry point — distinct from the
file/folder bulk-delete flow ELITEA-1847 already covers — confirming the
dot-menu reuses the identical shared ``DeleteEntityModal`` component from a
different call site, against a different underlying DELETE endpoint.

Test flow:
1. Navigate to Artifacts.
2. Click "+ Artifact Bucket" — full page navigation to
   ``/artifacts/create-bucket``, not a modal.
3. Verify the "New Bucket" form's fields and their defaults.
4. Fill the Name field with the case's own literal 56-character name — its
   exact length IS the test subject (CLARIFICATION #667: the case's own
   label calls it "55 chars"; ``len(...)`` on the literal value is 56).
5. Verify no character-limit warning (``aria-invalid`` is not ``"true"``).
6. Leave Retention at its default.
7. Click Save — verifies the bucket-creation POST returns 200.
8. Verify the bucket appears in the left-panel bucket list.
9. Hover the bucket row and open its 3-dot actions menu.
10. Verify the dropdown's full text shows all 4 items — LIVE label/order
    (CLARIFICATION #666: "Rename", not "Edit"; Upload files/Rename/Pin to
    top/Delete order, not the case's stale "...Pin to top, Edit, Delete").
11. Click "Delete" in the open dropdown — verifies the delete-confirmation
    modal opens.
12. Verify the modal's heading and message — LIVE wording (CLARIFICATION
    #664: "...to delete the {name}? ..." — the case's own text drops "the").
13. Click "Delete" in the modal — verifies the bucket-DELETE (a
    query-parameter URL shape, ``?name=...``) returns 200.
14. Verify the success toast — LIVE wording (CLARIFICATION #665: includes
    the bucket name and differs in word order from the case's own text).
15. Verify the bucket is no longer listed.

Overlap check (see AFS): no existing test exercises the 55/56-char boundary
length, and no existing test drives bucket-level deletion via the UI — the
only bucket-deletion path elsewhere in the suite is
``ArtifactAPI.delete_bucket()`` in test teardowns (API-only, a different
code path, known to 404 regardless per #636 — not this case's concern).

AFS: test-specs/artifacts/l3_create-artifact-bucket-55-char-name-and-delete_ELITEA-1817.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches case priority — AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_create_bucket_55char_name_and_delete.py -v
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, menus, rows
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions, bucket-list refetch
DELETE_RESPONSE_TIMEOUT = 15_000   # DELETE request + response

# The case's own literal bucket name — NOT a placeholder (unlike sibling
# ELITEA-1808/1832/1839's generated names). This exact string's length IS
# the test subject; do not generate a fresh/unique variant.
BUCKET_NAME = "bucket-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y"

# Data-accuracy note (CLARIFICATION #667): the case labels this string
# "(55 chars)" but its actual length is 56 — this is the real max-length
# boundary (CreateBucket.jsx's yup schema: `.max(56, ...)`), not "one below
# max" as the case's own framing implies. Assert the actual length, not the
# case's stale "55" label.
EXPECTED_BUCKET_NAME_LENGTH = 56

# Live-confirmed dropdown text (implementer + analyst exploration,
# ELITEA-1817). CLARIFICATION #666: the case's own text says "Upload
# files, Pin to top, Edit, Delete"; the live label is "Rename" (not
# "Edit") and the live order is Upload files/Rename/Pin to top/Delete.
# Reverse-masking guard: assert the product's live contract, not the
# case's stale wording.
EXPECTED_MENU_ITEMS_TEXT = "Upload filesRenamePin to topDelete"

# Live-confirmed text — both deliberately differ from the TMS case's own
# (stale) wording; reverse-masking guard, same pattern as ELITEA-1847's
# #659/#660. CLARIFICATION #664 (dialog wording) / #665 (toast wording).
EXPECTED_CONFIRM_MESSAGE = f"Are you sure to delete the {BUCKET_NAME}? It can't be restored."
EXPECTED_SUCCESS_TOAST = f"The {BUCKET_NAME} bucket has been successfully deleted."


@allure.epic("Artifacts")
@allure.feature("Bucket Creation + Delete Flow")
class TestArtifactCreateBucketMaxLengthNameAndDelete:
    """ELITEA-1817 — Create a bucket at the 56-char name boundary and delete
    it via the bucket-row dot-menu's 'Delete' entry point.

    Bucket is created BY the test itself and deleted BY the test itself
    (Test Steps 11-15 are the case's own subject) — no ``artifact_bucket``
    fixture is used and no teardown deletion is needed on the happy path;
    only a ``try``/``finally`` fail-safe guards against a bucket being left
    behind if an assertion fails mid-test (workflow skill Hard Rule 10 /
    AFS § Cleanup).
    """

    @pytest.mark.p2
    @allure.title(
        "Create a bucket with a 56-character name (no char-limit warning) "
        "and delete it via the bucket-row dot-menu"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1817_create-artifact-bucket-55-char-name-and-delete.md",
        "onetest-ai Test Case link",
    )
    def test_create_bucket_max_length_name_and_delete(self, page, artifact_api):
        """Create a bucket at the 56-char boundary, then delete it via the
        bucket-row dot-menu.

        The bucket is the test's own mutation, created AND deleted via the
        UI within the test itself — the case's own core subject IS the
        deletion (Test Steps 11-15), so there is no teardown deletion to
        perform on the happy path; only a fail-safe try/finally guards a
        partial run.
        """
        assert len(BUCKET_NAME) == EXPECTED_BUCKET_NAME_LENGTH, (
            f"Test data sanity check: expected the literal bucket name to be "
            f"{EXPECTED_BUCKET_NAME_LENGTH} chars (CLARIFICATION #667 — the "
            f"case's own '55 chars' label is inaccurate), got "
            f"{len(BUCKET_NAME)}"
        )

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)

        try:
            with allure.step("Step 1 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()

            with allure.step(
                "Step 2 — Click the '+ Artifact Bucket' button — verify it "
                "opens the 'New Bucket' form as a full page, not a modal"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in artifacts_page.page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {artifacts_page.page.url!r}"
                )

            with allure.step(
                "Step 3 — Verify the 'New Bucket' form is visible with all "
                "required fields, pre-filled with their defaults"
            ):
                assert artifacts_page.bucket_name_input.input_value() == "new-bucket", (
                    "Name field should be pre-filled with the literal default "
                    "'new-bucket' on a fresh form load"
                )
                assert (
                    artifacts_page.bucket_retention_measure_combobox.text_content() or ""
                ).strip() == "Years", "Retention measure should default to 'Years'"
                assert artifacts_page.bucket_retention_value_input.input_value() == "1", (
                    "Retention value should default to '1'"
                )
                assert artifacts_page.bucket_save_button.is_visible(), (
                    "Save button should be visible on the 'New Bucket' form"
                )

            with allure.step(
                "Step 4 — Enter the 56-character bucket name — verify the "
                "field displays it exactly, at its full length"
            ):
                artifacts_page.fill_bucket_name(BUCKET_NAME)
                filled_value = artifacts_page.bucket_name_input.input_value()
                assert filled_value == BUCKET_NAME, (
                    f"Name field should show the full bucket name {BUCKET_NAME!r} "
                    f"after filling, got: {filled_value!r}"
                )
                assert len(filled_value) == EXPECTED_BUCKET_NAME_LENGTH, (
                    "Name field's value should be the full "
                    f"{EXPECTED_BUCKET_NAME_LENGTH}-char name (see the "
                    "data-accuracy note — CLARIFICATION #667 — do not assert "
                    f"55), got length {len(filled_value)}"
                )

            with allure.step(
                "Step 5 — Verify no character-limit warning is displayed for "
                "the full-length name"
            ):
                assert not artifacts_page.is_bucket_name_invalid(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "Name field should NOT be flagged invalid "
                    "(aria-invalid='true') at the 56-char boundary length"
                )

            with allure.step(
                "Step 6 — Leave Retention policy as default — verify it is "
                "still Years/1 after filling the name"
            ):
                assert (
                    artifacts_page.bucket_retention_measure_combobox.text_content() or ""
                ).strip() == "Years", "Retention measure should remain 'Years'"
                assert artifacts_page.bucket_retention_value_input.input_value() == "1", (
                    "Retention value should remain '1'"
                )

            with allure.step("Step 7 — Click Save"):
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got: "
                    f"{create_response.status} for {create_response.url}"
                )

            with allure.step(
                "Step 8 — Verify the bucket appears in the left-panel bucket "
                "list — condition-based wait on the bucket's own dynamic "
                "testid, never an immediate assertion right after Save (a "
                "snapshot taken too early can catch the bucket list "
                "mid-refetch)"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    BUCKET_NAME, timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                "Step 9 — Hover the bucket row and click its 3-dot actions "
                "menu trigger — verify the dropdown opens"
            ):
                artifacts_page.open_bucket_menu(BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert artifacts_page.bucket_menu_upload_files_menuitem.is_visible(), (
                    "Bucket-menu dropdown should be open (proven by the "
                    "'Upload files' item's visibility)"
                )

            with allure.step(
                "Step 10 — Verify the dropdown shows all 4 items — LIVE "
                "label/order (CLARIFICATION #666 — case's own text says "
                "'Upload files, Pin to top, Edit, Delete'; live label is "
                "'Rename' and live order is Upload files/Rename/Pin to "
                "top/Delete — reverse-masking guard: assert the product's "
                "live contract, not the case's stale wording)"
            ):
                menu_text = artifacts_page.get_bucket_menu_items_text(
                    BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert menu_text == EXPECTED_MENU_ITEMS_TEXT, (
                    f"Expected the bucket-menu dropdown's live text to be "
                    f"{EXPECTED_MENU_ITEMS_TEXT!r}, got {menu_text!r}"
                )

            with allure.step(
                "Step 11 — Click 'Delete' in the open dropdown — verify the "
                "delete-confirmation modal opens"
            ):
                artifacts_page.click_bucket_menu_delete_item(timeout=UI_ELEMENT_TIMEOUT)
                expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 12 — Verify the 'Delete confirmation' modal shows the "
                "correct message and the Delete button (message wording is "
                "CLARIFICATION #664 — live text asserted, not the case's "
                "stale wording; reverse-masking guard, same root component "
                "ELITEA-1847 already flagged for a sibling wording drift, "
                "#659)"
            ):
                dialog_text = artifacts_page.delete_confirm_dialog.text_content() or ""
                assert "Delete confirmation" in dialog_text, (
                    f"Expected the modal heading 'Delete confirmation' "
                    f"somewhere in the dialog's text, got: {dialog_text!r}"
                )
                message_text = artifacts_page.get_delete_confirm_message_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert message_text == EXPECTED_CONFIRM_MESSAGE, (
                    f"Expected live confirm message {EXPECTED_CONFIRM_MESSAGE!r}, "
                    f"got {message_text!r}"
                )
                assert artifacts_page.delete_confirm_button.is_visible(), (
                    "'Delete' (confirm) button should be visible in the modal"
                )

            with allure.step(
                "Step 13 — Click the 'Delete' button in the modal — verify "
                "the bucket-DELETE (query-parameter URL shape) returns 200"
            ):
                delete_response = artifacts_page.confirm_delete_bucket(
                    timeout=DELETE_RESPONSE_TIMEOUT,
                )
                assert delete_response.status == 200, (
                    f"Expected bucket DELETE to return 200, got "
                    f"{delete_response.status} for {delete_response.url}"
                )
                assert f"name={BUCKET_NAME}" in delete_response.url, (
                    f"Expected the DELETE URL's query param to name the "
                    f"deleted bucket, got: {delete_response.url!r}"
                )

            with allure.step(
                "Step 14 — Verify the success notification shows the LIVE "
                "text (CLARIFICATION #665 — case's own text says 'The "
                "bucket has been deleted successfully'; live text includes "
                "the bucket name and differs in word order; reverse-masking "
                "guard, same root pattern as ELITEA-1847's own toast-wording "
                "CLARIFICATION #660)"
            ):
                expect(artifacts_page.success_toast_message).to_have_text(
                    EXPECTED_SUCCESS_TOAST, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 15 — Verify the bucket is no longer listed"):
                artifacts_page.wait_for_bucket_removed_from_list(
                    BUCKET_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert artifacts_page.count_bucket_rows(BUCKET_NAME) == 0, (
                    f"'{BUCKET_NAME}' should no longer be listed after deletion"
                )

            with allure.step(
                "Side-channel check — no console errors across the whole "
                "create-bucket + delete flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the create-bucket + "
                    f"delete flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Fail-safe only — the case's own core subject IS the deletion
            # (Test Steps 11-15), so on a clean pass the bucket is already
            # gone before this runs. Guards against a bucket being left
            # behind if an assertion fails mid-test (e.g. after creation but
            # before the delete-confirm click). Known pre-existing defect
            # (#636, not new to this case): delete_bucket() 404s in the
            # current dev environment regardless (its path-segment URL
            # shape differs from the UI's own query-param shape — see AFS
            # § Known Defects Found) — do not treat "the delete call ran" /
            # a 404 here as proof of anything about THIS case, out of scope
            # to fix here.
            try:
                artifact_api.delete_bucket(BUCKET_NAME)
                logger.info("Fail-safe cleanup: deleted bucket '%s'", BUCKET_NAME)
            except Exception as exc:
                logger.info(
                    "Fail-safe cleanup no-op or already-gone for '%s' (known "
                    "defect #636 — delete_bucket() 404s in dev regardless): "
                    "%s", BUCKET_NAME, exc,
                )
