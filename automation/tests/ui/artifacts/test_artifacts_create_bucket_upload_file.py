"""UI Test for ELITEA-1808 — Create Artifact Bucket via "+ Artifact Bucket"
Button (Path 1) and Upload File.

Regression test: verifies the primary bucket-creation flow through the
"+ Artifact Bucket" full-page form (``/artifacts/create-bucket``), then
uploads a file to the newly created bucket via the bucket-row 3-dot menu's
"Upload files" item — a different entry point from the already-automated
toolbar upload button (ELITEA-1832/ELITEA-1839) — and confirms the file
appears in both the right-panel file table and the left-panel tree.

Test flow:
1. Navigate to Artifacts.
2. Click "+ Artifact Bucket" — a full page navigation to
   ``/artifacts/create-bucket``, not a modal.
3. Verify the "New Bucket" form's fields and their defaults (Name
   pre-filled "new-bucket", Retention "Years"/"1", Save visible).
4. Replace the Name field with a generated unique bucket name (MUI field —
   select-all via ``select_text()`` + ``type()``, not a bare ``fill()``).
5. Leave Retention at its default.
6. Click Save — verifies the bucket-creation POST returns 200.
7. Wait (condition-based, not a fixed sleep or an immediate assertion) for
   the new bucket's own dynamic dot-menu testid to appear in the left panel.
8. Hover the bucket row and open its 3-dot actions menu.
9-12. Click "Upload files" in that menu, select ``test.txt`` via the native
   file chooser (one mechanically inseparable Playwright action).
13. Verify the "Upload files to ..." modal opens with the Path pre-filled
    with the bucket name.
14. Click Upload — verifies the upload PUT returns 200.
15. Verify the upload completes: ``test.txt`` appears in the file table.
16. Verify ``test.txt``'s row shows the correct Type ("Text"), Size (exact
    byte count), and a "Last update" timestamp matching a date-pattern
    regex (not an exact value — the clock differs per run). Correction:
    the original analyst pass claimed no timestamp column existed
    (CLARIFICATION #642) — that was a viewport artifact, not a real
    absence; see the round-2 fix note above ``LAST_UPDATE_TIMESTAMP_PATTERN``.
17. Verify ``test.txt`` also appears in the left-panel bucket tree.

AFS: test-specs/artifacts/l2_create-bucket-path1-and-upload-file_ELITEA-1808.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority — AFS l2/"high")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_create_bucket_upload_file.py -v
"""

import logging
import re
import time

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000       # fields, buttons, menus, rows
NAVIGATION_TIMEOUT = 15_000       # SPA route transitions, bucket-list refetch
# ELITEA-1808 AFS step-15 fidelity caveat: the upload path was not
# independently confirmed to show a toast in the analyst's run (only the
# separate bucket-creation toast was confirmed in source) — a short POLLED
# window (Playwright's auto-retrying wait_for, not a raw sleep or a single
# instantaneous DOM read) records whether it appeared, informationally only.
TOAST_INFORMATIONAL_POLL_TIMEOUT = 2_000

FILE_NAME = "test.txt"
FILE_CONTENT = b"Sample content for ELITEA-1808 create-bucket + upload test.\n"

# ELITEA-1808 round-2 review fix: the file table DOES have a real "Last
# update" timestamp column (round-1 analyst missed it — a narrower viewport
# clipped it off-screen; confirmed live at 1600x900 by both the round-2
# reviewer and the orchestrator). Pattern only, never an exact value — the
# clock differs per run. Observed live format: "DD-MM-YYYY, HH:MM AM/PM".
LAST_UPDATE_TIMESTAMP_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)")


def _generate_bucket_name(node_name: str) -> str:
    """Generate a unique bucket name matching this project's existing naming
    scheme (``automation/fixtures/data_fixtures.py``'s ``artifact_bucket``
    fixture) — reimplemented here rather than reusing that fixture, because
    per the AFS this case's own subject IS the UI-driven creation, so the
    bucket must not already exist when the test starts (§ Test Data).
    """
    ts = str(int(time.time() * 1000))[-6:]
    raw = f"autotest-{node_name}"
    safe = raw.lower().replace("_", "-").replace("[", "").replace("]", "")[:40]
    return f"{safe}-{ts}"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation + Upload Flow")
class TestArtifactCreateBucketAndUploadFile:
    """ELITEA-1808 — Create a bucket via the '+ Artifact Bucket' form and
    upload a file via the bucket-row dot-menu's 'Upload files' entry point.

    Bucket is created BY the test itself (Test Steps 2-7 are the case's own
    subject, not a precondition) — no ``artifact_bucket`` fixture is used;
    the bucket name is generated in setup and deleted in a manual teardown.
    """

    @pytest.mark.p1
    @allure.title(
        "Create a bucket via the '+ Artifact Bucket' form and upload a file "
        "via the bucket-row dot-menu"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1808_create-artifact-bucket-path-1-and-upload-file.md",
        "onetest-ai Test Case link",
    )
    def test_create_bucket_via_form_and_upload_file_via_bucket_menu(
        self, page, artifact_api, tmp_path, request,
    ):
        """Create a bucket via the form, upload a file via the bucket-menu.

        The bucket is the test's own mutation (created via the UI, deleted
        in teardown) — the minimal state this observable inherently
        requires (workflow skill Hard Rule 10): the case's own subject IS
        bucket creation, so there is no pre-existing stable bucket to
        assert against read-only.
        """
        bucket_name = _generate_bucket_name(request.node.name)

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        file_path = tmp_path / FILE_NAME
        file_path.write_bytes(FILE_CONTENT)

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
                "Step 4 — Enter the generated bucket name — verify the field "
                "displays it exactly"
            ):
                artifacts_page.fill_bucket_name(bucket_name)
                assert artifacts_page.bucket_name_input.input_value() == bucket_name, (
                    f"Name field should show the generated name {bucket_name!r} "
                    f"after filling"
                )

            with allure.step(
                "Step 5 — Leave Retention policy as default — verify it is "
                "still Years/1 after filling the name"
            ):
                assert (
                    artifacts_page.bucket_retention_measure_combobox.text_content() or ""
                ).strip() == "Years", "Retention measure should remain 'Years'"
                assert artifacts_page.bucket_retention_value_input.input_value() == "1", (
                    "Retention value should remain '1'"
                )

            with allure.step("Step 6 — Click Save"):
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got: "
                    f"{create_response.status} for {create_response.url}"
                )

            with allure.step(
                "Step 7 — Verify the generated bucket appears in the left-panel "
                "bucket list — condition-based wait on the bucket's own dynamic "
                "testid, never an immediate assertion right after Save (a "
                "snapshot taken too early can catch the bucket list mid-refetch)"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                "Step 8 — Hover the bucket row and click its 3-dot ellipsis "
                "menu — verify the dropdown opens (this case's own scope: "
                "'Upload files' — 'Rename'/'Pin to top'/'Delete' have no "
                "testid added, per the AFS's documented scope ruling)"
            ):
                artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                assert artifacts_page.bucket_menu_upload_files_menuitem.is_visible(), (
                    "'Upload files' item should be visible once the bucket "
                    "row's dot-menu is open"
                )

            with allure.step(
                "Steps 9-12 — Select 'Upload files' from the dropdown; select "
                "test.txt via the native file explorer; confirm the selection "
                "(one mechanically inseparable Playwright action — the click, "
                "the chooser firing, and set_files() ARE the confirm)"
            ):
                artifacts_page.click_bucket_menu_upload_files_item(
                    [str(file_path)], timeout=NAVIGATION_TIMEOUT,
                )

            with allure.step(
                "Step 13 — Verify the 'Upload files to ...' modal opens with "
                "the Path field pre-filled with the bucket name"
            ):
                artifacts_page.wait_for_upload_path_dialog(timeout=UI_ELEMENT_TIMEOUT)
                path_text = artifacts_page.get_upload_path_prefix_text()
                assert bucket_name in path_text, (
                    f"Path field should show the bucket name {bucket_name!r} "
                    f"as its prefix, got: {path_text!r}"
                )

            with allure.step("Step 14 — Click the Upload button in the modal"):
                upload_response = artifacts_page.click_upload_path_upload_button_and_capture_response(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert upload_response.status == 200, (
                    f"Upload PUT should return 200, got: {upload_response.status} "
                    f"for {upload_response.url}"
                )

            with allure.step(
                "Step 15 — Verify the upload completes successfully (primary: "
                "test.txt appears in the file table; secondary/fidelity-caveat "
                "per the AFS: a generic success toast may briefly appear — "
                "checked informationally only, never as the pass condition)"
            ):
                assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"'{FILE_NAME}' should appear in the file table after upload"
                )
                # Secondary/informational signal only (AFS Test Step 15
                # fidelity caveat) — the upload path was never independently
                # confirmed to show a toast, so its absence is NOT a failure;
                # a short polled wait (never a single instantaneous DOM read)
                # just records whether it happened to appear.
                try:
                    artifacts_page.success_toast_message.wait_for(
                        state="visible", timeout=TOAST_INFORMATIONAL_POLL_TIMEOUT,
                    )
                    logger.info(
                        "Informational: success toast observed after upload "
                        "(not required by this case — AFS fidelity caveat)"
                    )
                except PlaywrightTimeoutError:
                    logger.info(
                        "Informational: no success toast observed after "
                        "upload within %dms (not confirmed to fire for "
                        "uploads — AFS fidelity caveat, not a failure)",
                        TOAST_INFORMATIONAL_POLL_TIMEOUT,
                    )

            with allure.step(
                "Step 16 — Verify test.txt appears in the file table with the "
                "correct Type, Size, and Last-update timestamp"
            ):
                row_text = artifacts_page.get_file_row_text(
                    FILE_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "Text" in row_text, (
                    f"File row should show Type 'Text' for a .txt file, row "
                    f"text was: {row_text!r}"
                )
                expected_size = f"{len(FILE_CONTENT)} B"
                assert expected_size in row_text, (
                    f"File row should show Size {expected_size!r} (exact byte "
                    f"count), row text was: {row_text!r}"
                )
                # Round-2 review fix: the "Last update" column IS real and
                # visible (see LAST_UPDATE_TIMESTAMP_PATTERN comment above) —
                # assert its shape, not an exact value (the clock differs
                # per run).
                assert LAST_UPDATE_TIMESTAMP_PATTERN.search(row_text), (
                    f"File row should show a 'Last update' timestamp matching "
                    f"DD-MM-YYYY, HH:MM AM/PM, row text was: {row_text!r}"
                )
                file_count = artifacts_page.get_total_file_count_from_pagination()
                assert file_count == 1, (
                    f"Expected exactly 1 file in the freshly created bucket, "
                    f"got {file_count}"
                )

            with allure.step(
                "Step 17 — Verify test.txt is also listed in the left-panel "
                "tree under the generated bucket"
            ):
                artifacts_page.wait_for_file_in_tree(
                    FILE_NAME, timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                "Side-channel check — no console errors across the "
                "navigate → create-bucket → upload flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the create-bucket + "
                    f"upload flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Cleanup — known pre-existing defect (#636, already filed, not
            # new to this case): delete_bucket() 404s on both URL-format
            # attempts in the current dev environment, so the bucket will
            # likely leak. Do not treat "the delete call ran" as proof the
            # bucket is gone — out of scope to fix here (AFS § Cleanup).
            try:
                artifact_api.delete_bucket(bucket_name)
                logger.info("Deleted artifact bucket '%s'", bucket_name)
            except Exception as exc:
                logger.warning(
                    "Failed to delete artifact bucket '%s' (known defect "
                    "#636 — delete 404s in dev): %s", bucket_name, exc,
                )
