"""Chat Diagram Canvas Page — Mermaid CodeMirror source editor inside the
in-chat edit canvas (ELITEA-2088).

Owns only the Mermaid-editing-specific surface (the raw-source CodeMirror
editor). The canvas's shared chrome (title, close button, editing
indicator) lives in :class:`ChatCanvasPage`, composed on the same ``page``
(same pattern as ``McpCanvasPage`` + ``McpFormPage``).

SANCTIONED #579 EXCEPTION (third-party editor library internal render
nodes) — direct precedent match, no declared-improvisation flag needed
(AFS ELITEA-2088 § Concrete Handles): CodeMirror's per-line
``<div class="cm-line">`` nodes are library-internal, not app JSX — no
testid can be placed on them. Scoped raw selector under the testid-anchored
``editor_content`` parent, same shape already used by
``McpFormPage.fill_raw_json_line`` / ``PipelineDetailPage.edit_yaml_line``.
"""

import logging
import time

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.chat_diagram_canvas")

UI_ELEMENT_TIMEOUT = 10_000


class ChatDiagramCanvasPage(BasePage):
    """Page object for the Mermaid-source CodeMirror editor inside the chat edit canvas."""

    editor_content = LocatorDescriptor(
        testid="chat-canvas-mermaid-editor-content",
        description=(
            "CodeMirror wrapper Box around the raw Mermaid source editor "
            "(CanvasEditor.jsx's mermaidCodeEditorContainer)."
        ),
    )

    # Sanctioned #579 exception (module docstring) — CodeMirror's own
    # per-line render nodes, scoped as a child of the testid-anchored
    # editor_content parent.
    CM_LINE = ".cm-line"

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_editor(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Wait until the Mermaid CodeMirror editor is visible."""
        self.editor_content.wait_for(state="visible", timeout=timeout)
        logger.info("Mermaid editor visible")

    def get_source_lines(self) -> list[str]:
        """Return the editor's current source, one entry per ``.cm-line``."""
        lines = self.editor_content.locator(self.CM_LINE)
        return [lines.nth(i).text_content() or "" for i in range(lines.count())]

    @action("Replace a Mermaid source line")
    def replace_line(self, current_line_text: str, new_line_text: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Select and replace the ENTIRE ``.cm-line`` whose exact text is
        *current_line_text* with *new_line_text*.

        Mirrors ``McpFormPage.fill_raw_json_line`` / ``PipelineDetailPage.
        edit_yaml_line``'s click -> ``Home`` -> ``Shift+End`` -> type
        whole-line-replace mechanics, which gives precise control over
        WHERE new text lands within the line.

        DECLARED CORRECTION (Phase 2 exploration, AFS ELITEA-2088's own
        Blocked Steps flagged this exact sub-path as "not independently
        re-verified" — the implementer's first-pass confirmation item):
        the AFS's live-confirmed gesture for step 8 was click -> ``End``
        -> type (a bare APPEND at absolute end-of-line). Confirmed live
        THIS implementation that a bare append lands the new text AFTER
        the line's LAST token — on a compound connection line like
        ``A[Start] --> B{Decision}``, that is past the closing ``}``,
        outside any node's bracketed label, so it is syntactically valid
        (the diagram still re-renders without error) but never appears as
        rendered node text. Select-and-replace-whole-line, with the
        caller inserting the new text at the correct in-bracket position
        before calling this method, avoids that trap.

        Ambiguity caveat (same as ``edit_yaml_line``): ``get_by_text
        (exact=True)`` matches by DOM/document order — know your
        document's line uniqueness before relying on ``.first``.

        Args:
            current_line_text: Exact (trimmed) current text of the target
                line — never the diagram-type declaration line (line 1);
                see AFS § Test Data for why (breaks Mermaid syntax).
            new_line_text: Full replacement text for the line.
            timeout: Maximum wait time in milliseconds.
        """
        line = self.editor_content.get_by_text(current_line_text, exact=True).first
        line.wait_for(state="visible", timeout=timeout)
        line.click()
        self.page.keyboard.press("Home")
        self.page.keyboard.press("Shift+End")
        self.page.keyboard.type(new_line_text)
        self._wait_for_editor_text_stable(timeout_ms=timeout)
        logger.info("Replaced Mermaid source line %r -> %r", current_line_text, new_line_text)

    def _wait_for_editor_text_stable(self, stable_duration_ms: int = 150, timeout_ms: int = UI_ELEMENT_TIMEOUT) -> None:
        """Poll the editor's rendered text until it stops changing.

        Guards against CodeMirror's virtualized line rendering returning a
        stale read immediately after typing (confirmed live, AFS
        ELITEA-2088 § Known Defects Found — a same-session
        ``all_inner_texts()`` poll read stale text once despite the
        visible DOM having updated; screenshot evidence proved the edit
        had actually landed). Same idiom as
        ``McpFormPage._wait_for_text_content_stable``.
        """
        deadline = time.monotonic() + timeout_ms / 1000.0
        stable_duration = stable_duration_ms / 1000.0
        last_text = None
        stable_since = time.monotonic()
        while time.monotonic() < deadline:
            current_text = self.editor_content.text_content() or ""
            if current_text != last_text:
                last_text = current_text
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= stable_duration:
                return
            time.sleep(0.05)
