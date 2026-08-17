"""Toolkit Canvas Page — in-chat "+ Create New Toolkit" canvas panel (ELITEA-2083).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu -> Toolkits
-> "+ Create New Toolkit" (``ChatPage.open_create_new_toolkit_canvas()``).

The panel renders the SAME ``ToolkitForm``/``ToolkitTypeSelector`` component
set as the standalone toolkit-creation and MCP-creation flows.
``ToolkitCreationPage`` already owns the form-filling testids (``name_input``,
``type_search_input``, ``TOOLKIT_TYPE_CARD``, ``TOOLKIT_FIELD_INPUT``).
``ToolkitDetailPage`` owns the credential-dropdown testids
(``CREDENTIAL_SELECT_TRIGGER``, ``SELECT_OPTION``).  Per
``.agents/testing.md`` § Locator policy ("a data-testid should appear in
exactly one file"), this page object does NOT redeclare those fields —
compose ``ToolkitCreationPage(page)`` and ``ToolkitDetailPage(page)`` on the
same ``page`` for form filling (same composition pattern as
``McpCanvasPage`` + ``McpFormPage`` in
``test_create_mcp_from_conversation.py``).

This page object owns only the canvas-specific chrome that has no equivalent
in the existing toolkit page objects: the close (X) button, the title, and the
Create button.  These three testids were added to ``ToolkitEditor.jsx`` as
``isMcpTestIdScope``-conditional (false branch) props so the existing MCP path
(``mcp-canvas-*``) is untouched — see AFS Concrete Handles, commit
EliteaAI/EliteaUI@441333e1 on ``automation/testids``.
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.toolkit_canvas")


class ToolkitCanvasPage(BasePage):
    """Page object for the in-chat 'Create New Toolkit' canvas panel (ELITEA-2083)."""

    close_button = LocatorDescriptor(
        testid="toolkit-canvas-close-button",
        description=(
            "X (close) button on the Toolkit canvas panel header — threaded as "
            "BaseEditor/EditorHeader's optional closeButtonTestId prop, "
            "conditional on !isMcpTestIdScope at ToolkitEditor.jsx's "
            "<BaseEditor> call site (ELITEA-2083 add-data-testid, commit "
            "EliteaAI/EliteaUI@441333e1)."
        ),
    )

    title = LocatorDescriptor(
        testid="toolkit-canvas-title",
        description=(
            "Canvas heading.  Reads the toolkit's name once Create succeeds — "
            "threaded as BaseEditor/EditorHeader's optional titleTestId prop, "
            "conditional on !isMcpTestIdScope at ToolkitEditor.jsx."
        ),
    )

    create_button = LocatorDescriptor(
        testid="toolkit-canvas-create-button",
        description=(
            "'Create' button (CreateToolkitButton.jsx) — new optional "
            "testId prop, wired conditional on !isMcpTestIdScope at "
            "ToolkitEditor.jsx's call site (ELITEA-2083 add-data-testid, "
            "commit EliteaAI/EliteaUI@441333e1)."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (close button visible)."""
        self.close_button.wait_for(state="visible", timeout=timeout)
        logger.info("Toolkit canvas open")

    @action("Close Toolkit canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing Toolkit canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()
