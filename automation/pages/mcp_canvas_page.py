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

ELITEA-2084 — ``discard_button``/``discard_confirm_modal``/
``discard_confirm_button`` added, mirroring ``ToolkitCanvasPage``'s ELITEA-2081
shape 1:1 (same ``Button.DiscardButton``/``BaseModal`` components,
``isMcpTestIdScope``-conditional call site in ``ToolkitEditor.jsx``). The three
testid strings already existed on ``automation/testids`` before this change —
added as the MCP-branch mirror during ELITEA-2081's own Toolkit-canvas Discard
implementation (commit ``EliteaAI/EliteaUI@bc08563f``); this page object simply
never referenced them until now. No new ``add-data-testid`` work was required
(AFS test-specs/chat-interface/
l2_create-mcp-from-conversation-discard-changes_ELITEA-2084.md, Concrete
Handles). Confirming Discard on a freshly-selected, never-created MCP type
reverts the WHOLE canvas to the type-picker (``ToolkitEditor.jsx``'s
``handleDiscard`` creation-mode branch resets ``editToolDetail`` to ``null``
unconditionally, regardless of ``isMCP``) — not merely blank form fields.
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

    discard_button = LocatorDescriptor(
        testid="mcp-canvas-discard-button",
        description=(
            "Discard button in the MCP canvas header. Disabled until the "
            "form is dirty. Clicking it opens discard_confirm_modal "
            "(ELITEA-2084)."
        ),
    )

    discard_confirm_modal = LocatorDescriptor(
        testid="mcp-canvas-discard-confirm-modal",
        description="Discard confirmation modal (BaseModal) opened by discard_button.",
    )

    discard_confirm_button = LocatorDescriptor(
        testid="mcp-canvas-discard-confirm-button",
        description="Discard button inside the confirmation modal.",
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

    def is_discard_enabled(self, timeout: int = 5000) -> bool:
        """Return True if the canvas header's Discard button is enabled (form is dirty)."""
        self.discard_button.wait_for(state="visible", timeout=timeout)
        return self.discard_button.is_enabled()

    @action("Click Discard on MCP canvas")
    def click_discard(self, timeout: int = 5000) -> None:
        """Click the canvas header's Discard button, opening the confirmation modal (ELITEA-2084)."""
        logger.info("Clicking Discard on MCP canvas")
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.click()
        self.discard_confirm_modal.wait_for(state="visible", timeout=timeout)

    @action("Confirm discard on MCP canvas")
    def confirm_discard(self, timeout: int = 5000) -> None:
        """Click Discard inside the confirmation modal and wait for it to close (ELITEA-2084)."""
        logger.info("Confirming discard on MCP canvas")
        self.discard_confirm_button.click()
        self.discard_confirm_modal.wait_for(state="detached", timeout=timeout)
