"""MCP Canvas Page — in-chat "+ Create New MCP" canvas panel (ELITEA-2085).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu -> MCPs
-> "+ Create New MCP" (``ChatPage.open_create_new_mcp_canvas()``).

The panel renders the SAME ``ToolkitForm``/``ToolkitTypeSelector`` component
set as the standalone MCP-creation flow — ``McpFormPage`` already owns those
testids (``category_filter_tab``, ``remote_mcp_type_card``, ``name_input``,
``url_input``, ``client_secret_input_field``, ``connection_status``). Per
``.agents/testing.md`` § Locator policy ("a data-testid should appear in
exactly one file"), this page object does NOT redeclare those fields —
reuse ``McpFormPage(page)`` on the same ``page`` for form filling (same
composition pattern as ``AgentCanvasPage`` + ``AgentFormPage`` in
``test_create_agent_via_chat_canvas.py``).

This page object owns only the canvas-specific chrome that has no
``McpFormPage`` equivalent: the close (X) button, the title, and the Create
button (all threaded as ``isMCP``-conditional optional props on components
shared with the plain-Toolkit creation path — see AFS Concrete Handles /
declared improvisation).
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.mcp_canvas")


class McpCanvasPage(BasePage):
    """Page object for the in-chat 'Create New MCP' canvas panel."""

    close_button = LocatorDescriptor(
        testid="mcp-canvas-close-button",
        description=(
            "X (close) button on the MCP canvas panel header — threaded as "
            "BaseEditor/EditorHeader's optional closeButtonTestId prop, "
            "conditional on isMCP at ToolkitEditor.jsx's <BaseEditor> call "
            "site (ELITEA-2085 add-data-testid)."
        ),
    )

    title = LocatorDescriptor(
        testid="mcp-canvas-title",
        description=(
            "Canvas heading. Reads the MCP's name once Create succeeds — "
            "threaded as BaseEditor/EditorHeader's optional titleTestId "
            "prop, conditional on isMCP."
        ),
    )

    create_button = LocatorDescriptor(
        testid="mcp-canvas-create-button",
        description=(
            "'Create' button (CreateToolkitButton.jsx) — new optional "
            "testId prop, wired conditional on isMCP at ToolkitEditor.jsx's "
            "call site (declared improvisation, no prior precedent for "
            "this button — see AFS Concrete Handles)."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (close button visible)."""
        self.close_button.wait_for(state="visible", timeout=timeout)
        logger.info("MCP canvas open")

    @action("Close MCP canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing MCP canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()
