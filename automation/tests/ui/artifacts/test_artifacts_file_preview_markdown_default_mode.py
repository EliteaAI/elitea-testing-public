"""UI Test for ELITEA-1857 — File Preview/Edit: Markdown File Opens in
Preview Mode by Default with Save/Discard Inactive.

Regression test: verifies that opening a Markdown file in the editor shows
the render-mode toggle defaulting to "Preview" (pressed) with "Raw" not
pressed, the actual rendered Markdown structure (headings/bold/bullets, not
raw syntax), Save/Discard both DISABLED, no input accepted into the rendered
preview area, and the 3-dot actions menu still present/clickable.

Test flow:
1. Seed a fresh bucket (via API) with ``project-background.md`` (headings,
   bold span, bullet list).
2. Navigate to the bucket; verify the file table shows the file.
3. Verify the "View/Edit file" icon is visible on the row WITHOUT hovering
   (it is NOT hover-gated — EliteaAI/elitea-testing-public#994), then confirm
   it remains visible across a hover too.
4. Click the icon; verify the editor panel opens.
5. Verify the header shows the full path.
6. Verify the language label shows "Markdown (detected)".
7. Verify the render-mode toggle group: "Preview" (rendered) pressed,
   "Raw" (code) not pressed.
8. Verify the rendered content shows the actual heading/bold/bullet
   structure.
9. Verify Save and Discard are present and BOTH disabled.
10. Click into the rendered content and attempt to type a marker string;
    verify it never appears anywhere on the page (no input accepted).
11. Verify the 3-dot actions menu is present and clickable.
12. Verify no console errors across the open flow.

AFS: test-specs/artifacts/l3_file-preview-markdown-default-preview-mode_ELITEA-1857.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches AFS l3/"medium")

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_file_preview_markdown_default_mode.py -v
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
FILE_CONTENT = (
    b"# Project Overview\n\n"
    b"This is a **bold** statement about the project.\n\n"
    b"## Scope\n\n"
    b"Covers the automation of file preview features.\n\n"
    b"## Architecture\n\n"
    b"Uses a layered design.\n\n"
    b"## Key Components\n\n"
    b"- Component A\n"
    b"- Component B\n"
)
EXPECTED_HEADINGS = ["Project Overview", "Scope", "Architecture", "Key Components"]
NO_INPUT_MARKER = "AUTOTEST_NO_INPUT_MARKER_1857"


@allure.epic("Artifacts")
@allure.feature("File Preview/Edit")
class TestArtifactFilePreviewMarkdownDefaultMode:
    """ELITEA-1857 — A Markdown file opens in Preview mode by default,
    rendered, with Save/Discard inactive and editing blocked.
    """

    @pytest.mark.p2
    @allure.title(
        "Markdown file opens in Preview mode by default with Save/Discard inactive"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1857_file-preview-markdown-default-preview-mode.md",
        "onetest-ai Test Case link",
    )
    def test_markdown_file_opens_in_preview_mode_by_default(
        self, page, artifact_api, artifact_bucket,
    ):
        """A Markdown file opens with Preview active, rendered, editing blocked."""
        bucket_name = artifact_bucket["name"]

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        # ------------------------------------------------------------------
        # Precondition — seed project-background.md into the fresh bucket via API
        # ------------------------------------------------------------------
        artifact_api.upload_file(
            bucket_name, FILE_NAME, FILE_CONTENT, content_type="text/markdown",
        )

        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to the Artifacts section and select the fixture bucket"):
            artifacts_page.navigate_to_bucket(bucket_name, timeout=NAVIGATION_TIMEOUT)
            assert artifacts_page.file_exists(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                f"'{FILE_NAME}' should be visible in bucket '{bucket_name}'"
            )

        with allure.step(
            "Step 2 — Verify the 'View/Edit file' icon is visible WITHOUT "
            "hovering (not hover-gated), then confirm it stays visible "
            "across a hover too"
        ):
            # Regression guard for EliteaAI/elitea-testing-public#994: the icon
            # renders unconditionally (ArtifactRowActions.jsx has no hover-gated
            # opacity/visibility/display on the Preview IconButton). Asserting
            # BEFORE any hover call is what actually catches a future
            # hover-gating regression — asserting only post-hover (the AFS's
            # original, incorrect framing) can never distinguish "always
            # visible" from "hidden until hovered".
            assert artifacts_page.is_file_preview_button_visible(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            ), (
                "'View/Edit file' icon should be visible unconditionally, "
                "before any hover — it is NOT hover-gated "
                "(see EliteaAI/elitea-testing-public#994)"
            )
            artifacts_page.hover_file_row(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            assert artifacts_page.is_file_preview_button_visible(
                FILE_NAME, timeout=UI_ELEMENT_TIMEOUT
            ), "'View/Edit file' icon should remain visible after hovering the row"

        with allure.step("Step 3 — Click the icon; verify the editor panel opens"):
            artifacts_page.open_file_in_editor(FILE_NAME, timeout=UI_ELEMENT_TIMEOUT)
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Verify the panel header shows the full file path "
            "'<bucket>/project-background.md'"
        ):
            path_text = artifacts_page.get_file_preview_path_text(timeout=UI_ELEMENT_TIMEOUT)
            assert path_text == f"{bucket_name}/{FILE_NAME}", (
                f"Editor header should show the full path, expected "
                f"'{bucket_name}/{FILE_NAME}', got '{path_text}'"
            )

        with allure.step("Step 5 — Verify the language label shows 'Markdown (detected)'"):
            language_text = artifacts_page.get_file_preview_language_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert "Markdown" in language_text and "detected" in language_text, (
                f"Language label should show 'Markdown (detected)', got '{language_text}'"
            )

        with allure.step(
            "Steps 6-7 — Verify the render-mode toggle group is present: "
            "'Preview' pressed (active), 'Raw' not pressed"
        ):
            expect(artifacts_page.file_preview_mode_toggle_group).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_mode_toggle_rendered).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_mode_toggle_code).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            toggle_state = artifacts_page.get_file_preview_mode_toggle_state(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert toggle_state == {"rendered": "true", "code": "false"}, (
                f"'Preview' (rendered) should be the pressed default and 'Raw' "
                f"(code) unpressed, got {toggle_state}"
            )

        with allure.step(
            "Step 8 — Verify the file content is rendered as actual Markdown "
            "structure (headings, bold, bullet list), not raw syntax"
        ):
            rendered_text = artifacts_page.get_file_preview_markdown_content_text(
                timeout=UI_ELEMENT_TIMEOUT
            )
            for heading in EXPECTED_HEADINGS:
                assert heading in rendered_text, (
                    f"Rendered Markdown should show heading '{heading}': {rendered_text!r}"
                )
            rendered_html = artifacts_page.get_file_preview_markdown_content_html(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert "<h1" in rendered_html, (
                f"Rendered Markdown should contain a real <h1> element, not raw "
                f"'#' syntax: {rendered_html!r}"
            )
            assert "<h2" in rendered_html, (
                f"Rendered Markdown should contain real <h2> elements, not raw "
                f"'##' syntax: {rendered_html!r}"
            )
            assert "<strong" in rendered_html or "<b " in rendered_html or "<b>" in rendered_html, (
                f"Rendered Markdown should contain a real bold element, not raw "
                f"'**' syntax: {rendered_html!r}"
            )
            assert "<ul" in rendered_html and "<li" in rendered_html, (
                f"Rendered Markdown should contain a real bullet list, not raw "
                f"'-' syntax: {rendered_html!r}"
            )

        with allure.step(
            "Step 9 — Verify Save and Discard are present and BOTH DISABLED "
            "in Preview mode"
        ):
            expect(artifacts_page.file_preview_save_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(artifacts_page.file_preview_discard_button).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert artifacts_page.is_file_preview_save_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Save should be DISABLED in Preview mode"
            assert artifacts_page.is_file_preview_discard_disabled(
                timeout=UI_ELEMENT_TIMEOUT
            ), "Discard should be DISABLED in Preview mode"

        with allure.step(
            "Steps 10-11 — Click inside the rendered content and attempt to "
            "type text; verify no input is accepted anywhere on the page"
        ):
            artifacts_page.attempt_type_in_markdown_preview(
                NO_INPUT_MARKER, timeout=UI_ELEMENT_TIMEOUT
            )
            page_html = page.content()
            assert NO_INPUT_MARKER not in page_html, (
                f"Typed marker {NO_INPUT_MARKER!r} should never appear anywhere on "
                "the page — Preview mode does not accept input"
            )

        with allure.step(
            "Step 12 — Verify the 3-dot actions menu is present and clickable"
        ):
            expect(artifacts_page.file_preview_overflow_menu_button).to_be_enabled(
                timeout=UI_ELEMENT_TIMEOUT
            )
            artifacts_page.open_file_preview_actions_menu(timeout=UI_ELEMENT_TIMEOUT)
            menu_items = artifacts_page.get_file_preview_menu_item_labels(
                timeout=UI_ELEMENT_TIMEOUT
            )
            assert menu_items, "Editor panel menu should be openable and non-empty"
            page.keyboard.press("Escape")

        with allure.step("Side-channel check — no console errors during the open flow"):
            assert not console_errors, (
                f"Unexpected console errors during Markdown-preview open: "
                f"{[m.text for m in console_errors]}"
            )
