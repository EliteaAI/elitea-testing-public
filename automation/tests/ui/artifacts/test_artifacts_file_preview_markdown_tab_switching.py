"""UI Test for ELITEA-1861 — File Preview/Edit: Switching Between the
Preview and Raw Tabs for a Markdown file.

This is the **round-trip** case: Preview → Raw → **Preview again** → Raw,
with the original content intact and the Save/Discard states checked at every
point. It is entirely read-only — no edit, no modal, no save.

Two merged specs touch adjacent ground and neither covers the round trip:
``test_artifacts_file_preview_markdown_default_mode.py`` (ELITEA-1857) proves
Preview is the default; ``test_artifacts_file_preview_markdown_raw_edit_save.py``
(ELITEA-1858) proves the Preview → Raw switch. Neither asserts the switch
**back** to Preview, nor that the content survives the round trip
byte-for-byte — the idempotence observable this case owns.

Case-text divergence (steps 3 and 4): the case says Save and Discard "become
active" on the Raw tab and "become inactive again" back in Preview. They are
gated on ``hasUnsavedChanges``, not on render mode, and this case makes no
edit — so both stay DISABLED throughout. The live contract is asserted (which
matches the case's step-4 FINAL state, just not its premise); the case text is
filed as a clarification — EliteaAI/elitea-testing-public#1690.

Test flow:
1. Seed a fresh bucket (via API) with ``project-background.md``.
2. Open the file via the "View/Edit file" icon.
3. Verify the Preview default: toggle pressed, rendered Markdown mounted,
   CodeMirror NOT mounted, Save/Discard disabled.
4. Click "Raw": toggle flips, line-number gutter visible, rendered wrapper
   unmounted, Save/Discard still disabled. Capture the raw text.
5. Click "Preview": toggle flips back, CodeMirror unmounted, real rendered
   <h1>/<h2>/bold/<ul><li> structure back, Save/Discard still disabled.
6. Click "Raw" once more: the content is byte-equal to the step-4 capture.
7. Verify no console errors across the whole flow.

AFS: test-specs/artifacts/l3_file-preview-markdown-preview-raw-tab-switching_ELITEA-1861.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3 / case `priority: medium`)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_markdown_tab_switching.py -v
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
# Same content constant the merged ELITEA-1857/1858 Markdown specs use — it
# exercises every rendered-Markdown element the Preview assertions check.
FILE_CONTENT = (
    b"# Project Overview\n\n"
    b"This is a **bold** statement about the project.\n\n"
    b"## Scope\n\n"
    b"Covers the automation of file preview features.\n\n"
    b"## Key Components\n\n"
    b"- Component A\n"
    b"- Component B\n"
)

PREVIEW_TOGGLE_STATE = {"rendered": "true", "code": "false"}
RAW_TOGGLE_STATE = {"rendered": "false", "code": "true"}


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewMarkdownTabSwitching:
    """ELITEA-1861 — Preview ⇄ Raw tab switching is idempotent and lossless."""

    @pytest.mark.p2
    @allure.title(
        "Switching between the Preview and Raw tabs toggles the rendered "
        "branch without losing the original content"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1861_file-preview-markdown-switching-preview-raw-tabs.md",
        "onetest-ai Test Case link",
    )
    def test_switching_between_preview_and_raw_tabs(
        self, page, artifact_api, artifact_bucket,
    ):
        """Preview ⇄ Raw switching flips the mounted branch and preserves content."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed project-background.md into the fresh bucket via
        # API. The case's "bucket-1" is the case author's own environment;
        # this suite has no such fixture.
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
            expect(artifacts_page.file_preview_file_path).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 2 — Verify 'Preview' is active by default: the rendered "
            "Markdown wrapper is mounted, the CodeMirror content is NOT, and "
            "Save/Discard are both inactive"
        ):
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == PREVIEW_TOGGLE_STATE, (
                f"A Markdown file should open with Preview (rendered) pressed "
                f"by default, got {toggle_state}"
            )
            expect(artifacts_page.file_preview_markdown_content).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            # The two content branches are mutually exclusive MOUNTS, not
            # show/hide — `to_have_count(0)` is the correct assertion for "the
            # other view is gone" (AFS Automation Hints, live-confirmed).
            expect(artifacts_page.file_preview_code_content).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be DISABLED in the default Preview mode"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be DISABLED in the default Preview mode"

        with allure.step(
            "Step 3 — Click the 'Raw' tab: raw content with line numbers is "
            "shown, the rendered Markdown wrapper unmounts, and Save/Discard "
            "stay DISABLED (the case says they 'become active' — they are "
            "gated on unsaved changes, not on render mode, and this case "
            "makes no edit; see EliteaAI/elitea-testing-public#1690)"
        ):
            artifacts_page.click_file_preview_mode_toggle_code(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == RAW_TOGGLE_STATE, (
                f"After clicking Raw, 'code' should be pressed and 'rendered' "
                f"unpressed, got {toggle_state}"
            )
            assert artifacts_page.is_code_editor_line_numbers_visible(
                timeout=UI_ELEMENT_TIMEOUT
            ), "CodeMirror line-number gutter should be visible in Raw mode"
            expect(artifacts_page.file_preview_markdown_content).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should still be DISABLED after switching to Raw (no edit made)"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should still be DISABLED after switching to Raw (no edit made)"

        with allure.step(
            "Step 3a — Capture the raw content text (the round-trip oracle)"
        ):
            # `get_file_preview_content_text()` concatenates CodeMirror lines
            # with NO separator, so it cannot be indexed by line — but for a
            # whole-content byte-equality oracle that is exactly the right
            # shape (AFS Automation Hints).
            raw_content_before = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert raw_content_before, "Raw content text should not be empty"

        with allure.step(
            "Step 4 — Click the 'Preview' tab again: the CodeMirror content "
            "unmounts, real rendered Markdown structure is back, and "
            "Save/Discard are still DISABLED (the case says they 'become "
            "inactive again' — they were never active; #1690)"
        ):
            artifacts_page.click_file_preview_mode_toggle_rendered(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == PREVIEW_TOGGLE_STATE, (
                f"After clicking Preview, 'rendered' should be pressed and "
                f"'code' unpressed, got {toggle_state}"
            )
            expect(artifacts_page.file_preview_code_content).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )
            # "Formatted Markdown is shown" is otherwise satisfiable by a view
            # that merely prints the source text — assert real elements
            # (AFS Axis 2, same shape as the merged ELITEA-1857 spec).
            rendered_html = artifacts_page.get_file_preview_markdown_content_html(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert "<h1" in rendered_html, (
                f"Preview should contain a real <h1> element, not raw '#' "
                f"syntax: {rendered_html!r}"
            )
            assert "<h2" in rendered_html, (
                f"Preview should contain a real <h2> element, not raw '##' "
                f"syntax: {rendered_html!r}"
            )
            assert (
                "<strong" in rendered_html
                or "<b " in rendered_html
                or "<b>" in rendered_html
            ), (
                f"Preview should contain a real bold element, not raw '**' "
                f"syntax: {rendered_html!r}"
            )
            assert "<ul" in rendered_html and "<li" in rendered_html, (
                f"Preview should contain a real bullet list, not raw '-' "
                f"syntax: {rendered_html!r}"
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should still be DISABLED back in Preview mode"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should still be DISABLED back in Preview mode"

        with allure.step(
            "Step 5 — Switch back to 'Raw' and verify the original content is "
            "intact: byte-equal to the pre-round-trip capture (a substring "
            "check would pass even if the round trip dropped or duplicated "
            "lines)"
        ):
            artifacts_page.click_file_preview_mode_toggle_code(
                timeout=UI_ELEMENT_TIMEOUT
            )
            raw_content_after = artifacts_page.get_file_preview_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert raw_content_after == raw_content_before, (
                f"A Preview round trip must not alter the file content: "
                f"{raw_content_after!r} != {raw_content_before!r}"
            )

        with allure.step(
            "Side-channel check — no console errors during the tab-switching flow"
        ):
            assert not console_errors, (
                f"Unexpected console errors during Preview/Raw tab switching: "
                f"{[m.text for m in console_errors]}"
            )
