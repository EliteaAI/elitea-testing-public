"""Chat Canvas Page — shared "Edit table"/"Edit diagram"/"Edit code" canvas
chrome (ELITEA-2086/2087/2088).

Handles the right-side panel opened when a user clicks the pencil/edit icon
on a generated table (``MarkdownTableBlock.jsx``) or Mermaid diagram
(``MermaidCodeBlock.jsx``) inside a chat message. All three entry points
render the SAME ``CanvasEditHeader.jsx`` chrome (title, close button) and the
SAME ``EditingPlaceholder.jsx`` indicator in the conversation pane while the
canvas is open — this page object owns only that shared chrome, exactly as
``McpCanvasPage``/``PipelineCanvasPage`` own their own canvases' chrome.

Content-specific surfaces (the DataGrid table editor, the Mermaid CodeMirror
editor) are owned by ``ChatTableCanvasPage``/``ChatDiagramCanvasPage``
respectively — composed on the same ``page`` alongside this class, mirroring
the ``McpCanvasPage`` + ``McpFormPage`` composition pattern.

Testid gaps filled (``add-data-testid``, pushed to ``automation/testids``,
ELITEA-2086/2087/2088):
- ``chat-canvas-title`` / ``chat-canvas-close-button`` — ``CanvasEditHeader.jsx``'s
  title ``Typography`` and close ``IconButton`` (unconditional — this header
  has no MCP/Pipeline-style isMCP branching, it's the single shared
  in-message canvas chrome).
- ``chat-canvas-editing-indicator`` — ``EditingPlaceholder.jsx``'s bordered
  indicator ``Box`` (dynamic text via its ``title`` prop: "Table editing...",
  "Diagram editing...").
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.chat_canvas")


class ChatCanvasPage(BasePage):
    """Page object for the in-chat table/diagram/code edit canvas's shared chrome."""

    title = LocatorDescriptor(
        testid="chat-canvas-title",
        description=(
            "Canvas heading (CanvasEditHeader.jsx) — dynamic text: "
            "'Edit table' / 'Edit diagram' / 'Edit code' depending on the "
            "block type being edited."
        ),
    )

    close_button = LocatorDescriptor(
        testid="chat-canvas-close-button",
        description="X (close) button on the canvas panel header (CanvasEditHeader.jsx).",
    )

    editing_indicator = LocatorDescriptor(
        testid="chat-canvas-editing-indicator",
        description=(
            "Bordered indicator shown in the CONVERSATION pane (not the "
            "canvas) while a block is being edited (EditingPlaceholder.jsx). "
            "Dynamic text: 'Table editing...' / 'Diagram editing...'."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (close button visible)."""
        self.close_button.wait_for(state="visible", timeout=timeout)
        logger.info("Chat edit canvas open")

    @action("Close chat edit canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing chat edit canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()

    def get_editing_indicator_text(self, timeout: int = 10000) -> str:
        """Return the editing indicator's current text (e.g. 'Table editing...')."""
        self.editing_indicator.wait_for(state="visible", timeout=timeout)
        return self.editing_indicator.text_content() or ""
