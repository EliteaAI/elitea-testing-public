"""UI Test for ELITEA-2088 — Chat: Generate Mermaid Diagram and Open in
Canvas Mode.

Verifies that an AI-generated Mermaid diagram can be opened in the edit
canvas, that its raw Mermaid source is editable in a CodeMirror editor,
that a valid edit re-renders correctly, and that the edit syncs back to
the conversation's rendered diagram on close.

Spec: test-specs/chat-interface/l3_generate-mermaid-diagram-and-edit-in-canvas_ELITEA-2088.md

New page-object surface: ``ChatDiagramCanvasPage`` (Mermaid-source
CodeMirror editor) plus ``ChatPage.diagram_svg_container``/
``get_diagram_node_count``/``get_diagram_edge_count`` (the Mermaid-rendered
SVG, shared by the conversation view and the canvas's own live preview —
only one is ever mounted at a time). Reuses ``ChatCanvasPage`` (shared
canvas chrome) introduced for ELITEA-2086.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``):
- ``chat-diagram-edit-button`` (this case's own pencil icon,
  ``MermaidCodeBlock.jsx``).
- ``chat-canvas-mermaid-editor-content`` — CodeMirror wrapper Box
  (``CanvasEditor.jsx``).
- ``chat-mermaid-diagram-svg-container`` — the Mermaid-library SVG render
  target (``MermaidDiagramOutput/DiagramOutput.jsx``); the SVG itself is
  a sanctioned #579 exception (third-party widget subtree), scoped
  node/edge selectors (``.node``/``.edgePath``, standard Mermaid CSS
  classes) live as children of this testid.
- The shared canvas chrome (``chat-canvas-title``/``chat-canvas-close-
  button``/``chat-canvas-editing-indicator``) was added for ELITEA-2086 in
  the same PR; this case is a third consumer.
- ``.cm-line`` (CodeMirror per-line nodes, scoped inside
  ``chat-canvas-mermaid-editor-content``) is a DIRECT match to the
  existing sanctioned #579 exception (``mcp_form_page.py:121`` precedent)
  — no declared-improvisation flag needed, per the AFS's own framing.

Phase 2 exploration finding (not in the AFS's own Concrete Handles,
consistent with the same discovery made implementing the sibling case
ELITEA-2087): once a canvas-editable block has been through one edit-and-
close cycle, its conversation-pane render switches from a plain Markdown
"text_message" item to a "canvas_message" item rendered via ``Canvas.jsx``
(a SEPARATE, currently-untested pencil button, with the nested Markdown's
``showToolbar={false}`` hiding the original block's own toolbar). This
case's own step 11 assertion is therefore written against the diagram's
rendered SVG content, never against ``chat.diagram_edit_button``'s
visibility post-close.

Known defect handling: none — this case's happy path (node-label edit,
per AFS § Test Data automation guidance — never the diagram-type
declaration line) is fully clean. The real-time syntax-error path itself
(triggered by editing line 1) is confirmed working by the analyst's own
live exploration but is explicitly out of THIS case's scope (AFS step 9
note) — not automated here.

Flake stabilization (post-merge, gate hardening run): a transient Mermaid/
dagre ``<g> attribute transform: Expected number, "translate(undefined,
NaN)"`` console warning surfaced once during a batch gate run and did not
recur across 4 further standalone runs; every functional step in the
flagged run still passed. Classified as library-internal render-timing
noise, not a product defect — see ``_is_known_mermaid_transform_nan_warning``
for the source-level root cause and reproduction evidence.
"""

import logging

import allure
import pytest
from pages.chat_canvas_page import ChatCanvasPage
from pages.chat_diagram_canvas_page import ChatDiagramCanvasPage
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.generate_mermaid_diagram_and_edit_in_canvas")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p3, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
DIAGRAM_RENDER_TIMEOUT = 30_000
AI_RESPONSE_TIMEOUT = 60_000

MESSAGE_TEXT = "generate a mermaid diagram"
APPENDED_TEXT = " edited"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise (see
    ``test_edit_generated_table_canvas_open_and_verify_display.py``)."""
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_mermaid_transform_nan_warning(msg) -> bool:
    """Filter the Mermaid/dagre layout-race ``<g> transform`` console warning.

    Fired once (2x identical) during a batch hardening-gate run, then did not
    reproduce across an immediate standalone re-run nor 3 further standalone
    runs (this implementation's own investigation). In the ONE run where it
    fired, every one of this test's own functional steps (1-11: diagram
    renders with real node/edge counts, canvas opens, CodeMirror source
    shown, edit applied, diagram re-renders after the edit, conversation view
    reflects the edited text) still PASSED — the warning never coincided with
    a wrong rendered result, only with this side-channel console check.

    Root cause (read from source, ``EliteaUI/src/components/MermaidDiagramOutput/
    DiagramOutput.jsx``): this component mounts a FRESH ``id={diagramId}``
    Mermaid SVG target on every render (module-level ``diagramCount++`` in
    ``getDiagramId()``) and immediately re-initializes ``svg-pan-zoom`` on it.
    This case's flow renders (at least) three independent Mermaid instances —
    conversation step 3, the canvas's own live preview, and the conversation's
    step 11 re-render after close — each running dagre's layout pass before
    ``svg-pan-zoom`` reads element geometry. Mermaid/dagre's cluster and edge-
    label ``<g>`` nodes are a documented case (upstream mermaid-js/mermaid,
    e.g. #1846) where a ``getBBox()``-derived translate is computed one paint
    before the label's real dimensions are available, producing exactly this
    "Expected number, translate(undefined, NaN)" console error; per the SVG
    spec an invalid transform is dropped/ignored rather than breaking the
    element, which matches every functional assertion in the flagged run
    still holding. No prior filter for this signature existed anywhere in the
    suite (checked via ``grep -rn "translate(undefined" automation/`` before
    adding this one) — this establishes the category rather than following
    a precedent, per the same idiom as ``_is_known_secrets_403``: scoped to
    this exact message text, so any OTHER console error still fails the
    assertion below.
    """
    text = msg.text
    return "<g> attribute transform" in text and "translate(undefined, NaN)" in text


class TestGenerateMermaidDiagramAndEditInCanvas:
    """ELITEA-2088: Chat – Generate Mermaid Diagram and Open in Canvas Mode
    (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2088_chat-generate-mermaid-diagram-and-open-in-canvas-mode.md",
        "onetest-ai Test Case link",
    )
    def test_generate_mermaid_diagram_and_edit_in_canvas(self, page, conversation_id):
        """Generate a Mermaid diagram, open its edit canvas, edit a
        node-label source line (never the diagram-type declaration line),
        and verify the change syncs back to the conversation view.

        Steps (AFS
        test-specs/chat-interface/l3_generate-mermaid-diagram-and-edit-in-canvas_ELITEA-2088.md):
        1. Navigate to Chats and open a conversation.
        2. Send "generate a mermaid diagram".
        3. Verify the diagram renders with nodes/connections.
        4. Locate the pencil/edit icon.
        5. Click it; verify the canvas opens with heading "Edit diagram".
        6. Verify the Mermaid source is shown in a CodeMirror editor.
        7. Verify the "Diagram editing..." indicator.
        8. Edit one node-label line by appending " edited".
        9. Verify real-time syntax validation (happy path: the diagram
           stays valid/rendered after the edit).
        10. Close the canvas.
        11. Verify the edited text is reflected in the conversation's
            re-rendered diagram.
        """
        chat = ChatPage(page)
        canvas = ChatCanvasPage(page)
        diagram_canvas = ChatDiagramCanvasPage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not (
                _is_known_secrets_403(msg) or _is_known_mermaid_transform_nan_warning(msg)
            ):
                console_messages.append(msg)

        page.on("console", _on_console)

        with allure.step("Step 1 — Navigate to Chats and open a conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(f'Step 2 — Send "{MESSAGE_TEXT}"'):
            initial_count = chat.get_message_count()
            chat.send_message(MESSAGE_TEXT)
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_message_content_stable(stable_duration_ms=2000, timeout=30000)

        with allure.step(
            "Step 3 — Verify the diagram renders with nodes and connecting "
            "lines/arrows (structural presence, not exact node text/count "
            "— diagram content is AI-generated)"
        ):
            chat.wait_for_diagram_rendered(timeout=DIAGRAM_RENDER_TIMEOUT)
            node_count = chat.get_diagram_node_count()
            edge_count = chat.get_diagram_edge_count()
            assert node_count > 0, f"Expected at least one diagram node, got {node_count}"
            assert edge_count > 0, f"Expected at least one connecting edge, got {edge_count}"
            logger.info("Diagram rendered with %d node(s), %d edge(s)", node_count, edge_count)

        with allure.step("Step 4 — Locate the pencil/edit icon on the diagram"):
            expect(chat.diagram_edit_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 5 — Click the pencil icon; verify the canvas opens with '
            'heading "Edit diagram"'
        ):
            chat.click_diagram_edit_icon(timeout=UI_ELEMENT_TIMEOUT)
            canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.title).to_have_text("Edit diagram", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 6 — Verify the Mermaid source is shown in a CodeMirror editor"):
            diagram_canvas.wait_for_editor(timeout=UI_ELEMENT_TIMEOUT)
            source_lines = diagram_canvas.get_source_lines()
            assert len(source_lines) > 1, (
                f"Expected multiple Mermaid source lines (declaration + node/edge "
                f"definitions), got: {source_lines!r}"
            )

        with allure.step('Step 7 — Verify the "Diagram editing..." indicator is visible'):
            expect(canvas.editing_indicator).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.editing_indicator).to_contain_text(
                "Diagram editing...", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            'Step 8 — Edit one node-label line by inserting " edited" '
            "inside its bracketed label (NEVER the diagram-type "
            "declaration line 1 — breaks Mermaid syntax, AFS § Test Data)"
        ):
            # Target a line containing a bracketed node label ([...], {...},
            # (...)) and insert the text just before the closing bracket —
            # matching the AFS's own literal example (A[Start] --> B{...}
            # -> A[Start edited] --> B{...}). A bare append at absolute
            # end-of-line lands AFTER the line's last token on a compound
            # connection line, outside any node's label (Phase 2 exploration
            # finding — see ChatDiagramCanvasPage.replace_line docstring).
            target_index = next(
                i for i in range(1, len(source_lines))
                if source_lines[i].strip() and any(c in source_lines[i] for c in "[{(")
            )
            target_line = source_lines[target_index]
            # CodeMirror's Home goes to the first NON-whitespace character
            # (same caveat as PipelineDetailPage.edit_yaml_line) — build
            # the typed replacement WITHOUT the line's leading indentation,
            # since Home preserves it automatically; typing it back in
            # would double the indent (confirmed live, this implementation).
            stripped_line = target_line.lstrip()
            leading_ws = target_line[: len(target_line) - len(stripped_line)]
            bracket_pos = next(i for i, c in enumerate(stripped_line) if c in "]})")
            new_content = stripped_line[:bracket_pos] + APPENDED_TEXT + stripped_line[bracket_pos:]
            expected_full_line = leading_ws + new_content

            diagram_canvas.replace_line(target_line, new_content)
            edited_lines = diagram_canvas.get_source_lines()
            assert expected_full_line in edited_lines, (
                f"Expected {expected_full_line!r} among the edited source lines, got: {edited_lines!r}"
            )
            logger.info("Node-label line edited: %r -> %r", target_line, expected_full_line)

        with allure.step(
            "Step 9 — Verify real-time syntax validation: the diagram "
            "stays valid and re-renders (happy-path node-label edit, per "
            "AFS Automation Hints — the error/Quick-Fix path is a separate "
            "case's scope)"
        ):
            chat.wait_for_diagram_rendered(timeout=DIAGRAM_RENDER_TIMEOUT)
            assert chat.get_diagram_node_count() > 0, (
                "Diagram should still render nodes after a valid node-label edit"
            )

        with allure.step("Step 10 — Close the canvas window"):
            canvas.close(timeout=UI_ELEMENT_TIMEOUT)
            expect(canvas.close_button).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 11 — Verify the edited text is reflected in the "
            "conversation's re-rendered diagram"
        ):
            chat.wait_for_diagram_rendered(timeout=DIAGRAM_RENDER_TIMEOUT)
            diagram_text = chat.diagram_svg_container.text_content() or ""
            assert APPENDED_TEXT.strip() in diagram_text, (
                f"Expected the appended text {APPENDED_TEXT.strip()!r} to appear in "
                f"the re-rendered conversation diagram, got: {diagram_text!r}"
            )

        with allure.step(
            "Side-channel — verify no unexpected console errors occurred "
            "across the whole flow (known secrets-403 noise is pre-filtered)"
        ):
            assert not console_messages, (
                f"Unexpected console error(s) during the flow: {[m.text for m in console_messages]!r}"
            )
