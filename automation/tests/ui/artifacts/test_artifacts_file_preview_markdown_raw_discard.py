"""UI Tests for ELITEA-1859 / ELITEA-1860 — File Preview/Edit: the Discard
Warning modal's two exit paths for a **Markdown** file edited on the **Raw**
tab.

Family spec (one AFS, one parameterized test, one row per TMS case). Both
cases share the entire prefix — open ``project-background.md`` (which opens
in Preview), switch to the Raw tab, replace line 1 with ``# Modified
Heading``, click the header Discard button, assert the Warning modal — and
diverge on exactly one click:

* **ELITEA-1859** — confirm ("Discard"): the content reverts byte-for-byte to
  the original, the editor stays open **still on Raw**, Save/Discard stay
  visible but go back to disabled, and NO success notification appears.
* **ELITEA-1860** — dismiss ("Cancel"): the modal closes, the unsaved
  ``# Modified Heading`` survives, the editor stays **still on Raw**, and
  Save/Discard remain enabled.

Why this is a separate spec from the merged
``test_artifacts_file_preview_discard_warning.py`` (ELITEA-1853/1854): that
one exercises a ``.py`` file, which takes the editor's CODE branch and has
**no render-mode toggle at all** (``modeTogglerAvailable`` is false for code
files). The whole subject of ELITEA-1859/1860 is the Markdown + Raw-tab
dimension — that the toggle STAYS on Raw across the discard/cancel
round-trip rather than snapping back to Preview — an observable that is
asserted nowhere today.

Case-text divergence (ELITEA-1859 step 8): the case says Save and Discard
remain "still active" after confirming the discard. The live product
correctly re-disables both (``hasUnsavedChanges`` is reset by the revert).
The live contract is asserted; the case text is filed as a clarification —
EliteaAI/elitea-testing-public#1689.

AFS: test-specs/artifacts/l3_file-preview-markdown-raw-discard-modal-exit-paths_ELITEA-1859-1860.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3 / case `priority: medium`)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_markdown_raw_discard.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

FILE_NAME = "project-background.md"
# Same content constant the merged ELITEA-1857/1858 Markdown specs use, so
# line 1 is the unique heading "# Project Overview".
FILE_CONTENT = (
    b"# Project Overview\n\n"
    b"This is a **bold** statement about the project.\n\n"
    b"## Scope\n\n"
    b"Covers the automation of file preview features.\n\n"
    b"## Key Components\n\n"
    b"- Component A\n"
    b"- Component B\n"
)
ORIGINAL_HEADING = "# Project Overview"
MODIFIED_HEADING = "# Modified Heading"

WARNING_TITLE = "Warning"
WARNING_MESSAGE = "Are you sure you want to discard changes?"
CANCEL_LABEL = "Cancel"
DISCARD_LABEL = "Discard"

RAW_TOGGLE_STATE = {"rendered": "false", "code": "true"}

CASE_LINK_BASE = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/artifacts/"
)
# Real TMS case file names (verified against the cases repo, not guessed).
CASE_FILES = {
    "ELITEA-1859": "ELITEA-1859_file-preview-markdown-raw-discard-reverts.md",
    "ELITEA-1860": (
        "ELITEA-1860_file-preview-markdown-raw-cancel-discard-changes-intact.md"
    ),
}


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewMarkdownRawDiscard:
    """ELITEA-1859 / ELITEA-1860 — Markdown Raw-tab Discard Warning exits."""

    @pytest.mark.p2
    @pytest.mark.parametrize(
        (
            "case_id",
            "exit_method",
            "exit_label",
            "expect_change_present",
            "expect_buttons_enabled",
        ),
        [
            pytest.param(
                "ELITEA-1859",
                "confirm_file_preview_discard",
                DISCARD_LABEL,
                False,
                False,
                id="ELITEA-1859-confirm-discard-reverts-and-stays-on-raw-tab",
            ),
            pytest.param(
                "ELITEA-1860",
                "cancel_file_preview_discard",
                CANCEL_LABEL,
                True,
                True,
                id="ELITEA-1860-cancel-keeps-changes-and-stays-on-raw-tab",
            ),
        ],
    )
    @allure.title("Markdown Raw-tab Discard Warning modal — {case_id}")
    @allure.severity(allure.severity_level.NORMAL)
    def test_markdown_raw_discard_warning_exit_paths(
        self,
        page,
        artifact_api,
        artifact_bucket,
        case_id,
        exit_method,
        exit_label,
        expect_change_present,
        expect_buttons_enabled,
    ):
        """Exiting the Warning modal reverts (Discard) or preserves (Cancel), staying on Raw.

        Args:
            case_id: TMS case this row covers.
            exit_method: Page-object method that clicks this row's modal exit
                button and waits for the modal to close.
            exit_label: Visible label of that button ("Discard" / "Cancel").
            expect_change_present: Whether "# Modified Heading" survives the exit.
            expect_buttons_enabled: Whether Save/Discard stay enabled afterwards.
        """
        allure.dynamic.issue(
            f"{CASE_LINK_BASE}{CASE_FILES[case_id]}",
            f"onetest-ai Test Case link ({case_id})",
        )
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed project-background.md into the fresh bucket via
        # API. The case's "bucket-1" is the case author's own environment;
        # this suite has no such fixture, and both rows mutate in-editor
        # state, so each row gets its own bucket.
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/markdown",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step(
            "Step 1 — Navigate to Artifacts and open 'project-background.md' "
            "via the 'View/Edit file' icon"
        ):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            # Cheap guard that this file really took the toggle-bearing
            # Markdown branch: a regression to CODE-branch rendering would
            # make "click Raw" below silently meaningless (AFS Axis 2).
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == {"rendered": "true", "code": "false"}, (
                f"[{case_id}] A Markdown file must open with Preview (rendered) "
                f"pressed by default, got {toggle_state}"
            )

        with allure.step(
            "Step 2 — Click the 'Raw' tab to switch to raw editing mode"
        ):
            artifacts_page.click_file_preview_mode_toggle_code(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == RAW_TOGGLE_STATE, (
                f"[{case_id}] After clicking Raw, 'code' should be pressed and "
                f"'rendered' unpressed, got {toggle_state}"
            )

        with allure.step(
            "Step 2a — Capture the original editor content (the revert oracle "
            "for ELITEA-1859)"
        ):
            original_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert ORIGINAL_HEADING in original_content, (
                f"[{case_id}] Seeded heading '{ORIGINAL_HEADING}' should be in "
                f"the loaded content: {original_content!r}"
            )
            assert MODIFIED_HEADING not in original_content, (
                f"[{case_id}] Original content must not already contain the "
                f"change under test"
            )

        with allure.step(
            f"Step 3 — Replace line 1: '{ORIGINAL_HEADING}' becomes "
            f"'{MODIFIED_HEADING}'"
        ):
            artifacts_page.replace_file_preview_line_containing(
                ORIGINAL_HEADING, MODIFIED_HEADING, timeout=UI_ELEMENT_TIMEOUT
            )
            # Web-first pair — the original heading string occurs exactly once
            # in the seeded content, so "contains the new / no longer contains
            # the old" IS the line-1 replacement check. `get_file_preview_
            # content_text()` concatenates lines with no separator, so it
            # cannot be indexed by line (AFS Automation Hints).
            expect(artifacts_page.file_preview_code_content).to_contain_text(
                MODIFIED_HEADING, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_code_content).not_to_contain_text(
                ORIGINAL_HEADING, timeout=UI_ELEMENT_TIMEOUT
            )
            # Baseline for the ELITEA-1860 "change is intact" check: the FULL
            # editor content as it reads once the edit has landed. Captured
            # from the product, not reconstructed, so the later equality
            # assertion compares the product against itself.
            edited_content = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert MODIFIED_HEADING in edited_content, (
                f"[{case_id}] Post-edit baseline must carry the replaced "
                f"heading: {edited_content!r}"
            )

        with allure.step(
            "Step 3a — Verify Save and Discard became ENABLED (the product's "
            "own signal that the unsaved-changes state propagated past "
            "`useCodeMirror`'s 30ms `notifyChange` debounce — a correctness "
            "guard before clicking the header Discard, not a nicety)"
        ):
            assert artifacts_page.is_file_preview_save_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), f"[{case_id}] Save should be ENABLED once the editor has an unsaved edit"
            assert artifacts_page.is_file_preview_discard_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), (
                f"[{case_id}] Discard should be ENABLED once the editor has an "
                f"unsaved edit"
            )

        with allure.step(
            "Steps 4-5 — Click the header 'Discard' button and verify the "
            "'Warning' modal opens with the message "
            f"'{WARNING_MESSAGE}' (the header Discard never discards directly)"
        ):
            artifacts_page.click_file_preview_discard(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.file_preview_discard_warning_dialog).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_warning_title).to_have_text(
                WARNING_TITLE, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_warning_dialog).to_contain_text(
                WARNING_MESSAGE, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            f"Steps 6-7 — Click the modal's '{exit_label}' button ({case_id}) "
            "and verify the modal closes"
        ):
            getattr(artifacts_page, exit_method)(timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.file_preview_discard_warning_dialog).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 7a — Verify the file content matches this row's expectation "
            "(ELITEA-1859: reverted byte-for-byte to the original; "
            "ELITEA-1860: '# Modified Heading' still present)"
        ):
            # Web-first (auto-retrying) assertions first: the revert reaches
            # CodeMirror through a React state round-trip that completes
            # slightly AFTER the modal disappears, so an immediate one-shot
            # read races the product. Polling on the real observable is the
            # correct wait — never a sleep.
            if expect_change_present:
                expect(artifacts_page.file_preview_code_content).to_contain_text(
                    MODIFIED_HEADING, timeout=UI_ELEMENT_TIMEOUT
                )
            else:
                expect(artifacts_page.file_preview_code_content).not_to_contain_text(
                    MODIFIED_HEADING, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.file_preview_code_content).to_contain_text(
                    ORIGINAL_HEADING, timeout=UI_ELEMENT_TIMEOUT
                )
            content_after = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            if expect_change_present:
                # Stronger than "the marker survived" — byte-equality catches a
                # Cancel that silently drops or mangles any OTHER line while
                # leaving line 1 alone (AFS Axis 2).
                assert content_after == edited_content, (
                    f"[{case_id}] Cancel must leave the edited content intact "
                    f"byte-for-byte: {content_after!r} != {edited_content!r}"
                )
            else:
                # Byte-equality catches a revert that drops or mangles
                # unrelated lines (AFS Axis 2).
                assert content_after == original_content, (
                    f"[{case_id}] Discard must restore the ORIGINAL content "
                    f"byte-for-byte: {content_after!r} != {original_content!r}"
                )

        with allure.step(
            "Step 8 — Verify the editor remains open and the render-mode "
            "toggle is STILL on 'Raw' (the observable that makes these cases "
            "distinct from the code-file ELITEA-1853/1854 pair — the toggle "
            "must not snap back to Preview)"
        ):
            expect(artifacts_page.file_preview_file_path).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_code_content).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == RAW_TOGGLE_STATE, (
                f"[{case_id}] After exiting the Warning modal via "
                f"'{exit_label}', the editor must still be on the Raw tab, "
                f"got {toggle_state}"
            )

        with allure.step(
            "Step 8a — Verify Save and Discard are still visible, in this "
            "row's expected enabled state (ELITEA-1859: back to DISABLED, "
            "since the revert reset `hasUnsavedChanges` — the case text says "
            "'still active', which the live product contradicts, see "
            "EliteaAI/elitea-testing-public#1689; ELITEA-1860: still ENABLED)"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            if expect_buttons_enabled:
                assert artifacts_page.is_file_preview_save_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Save should remain ACTIVE after Cancel"
                assert artifacts_page.is_file_preview_discard_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Discard should remain ACTIVE after Cancel"
            else:
                assert artifacts_page.is_file_preview_save_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Save should be DISABLED again after Discard"
                assert artifacts_page.is_file_preview_discard_disabled(
                    timeout=UI_ELEMENT_TIMEOUT
                ), f"[{case_id}] Discard should be DISABLED again after Discard"

        if not expect_change_present:
            with allure.step(
                "Step 9 (ELITEA-1859) — Verify no success notification is "
                "displayed (discarding is a pure client-side state reset: no "
                "network request, no toast)"
            ):
                expect(artifacts_page.success_toast_message).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

        with allure.step(
            "Side-channel check — no console errors during the Markdown "
            "Raw-tab discard flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during the Markdown Raw-tab "
                f"discard flow: {[m.text for m in console_errors]}"
            )
