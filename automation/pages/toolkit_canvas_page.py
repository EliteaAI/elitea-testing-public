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
in the existing toolkit page objects: the close (X) button, the title, the
Create button, and (ELITEA-2081) the create-mode Discard button + its
confirmation modal.  These testids were added to ``ToolkitEditor.jsx`` as
``isMcpTestIdScope``-conditional (false branch) props so the existing MCP path
(``mcp-canvas-*``) is untouched — see AFS Concrete Handles, commit
EliteaAI/EliteaUI@441333e1 on ``automation/testids``.

ELITEA-2081 — ``discard_button``/``discard_confirm_modal``/
``discard_confirm_button`` added, mirroring ``PipelineCanvasPage``'s
ELITEA-2076 fix exactly: ``BaseEditor.jsx``/``EditorHeader.jsx`` already
threaded the ``discardButtonTestId``/``discardModalTestId``/
``discardConfirmButtonTestId`` optional props end-to-end (added for
``PipelineEditor.jsx`` by ELITEA-2076) and ``ToolkitEditor.jsx`` already had
a working ``handleDiscard`` wired to ``BaseEditor``'s ``onDiscard`` — only
the three testid props were missing at this call site.  Added commit
EliteaAI/EliteaUI@bc08563f on ``automation/testids``
(``toolkit-canvas-discard-button``, ``toolkit-canvas-discard-confirm-modal``,
``toolkit-canvas-discard-confirm-button``; ``mcp-canvas-*`` mirrors, same
``isMcpTestIdScope`` conditional as the other three chrome testids).
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

    discard_button = LocatorDescriptor(
        testid="toolkit-canvas-discard-button",
        description=(
            "Discard button in the Toolkit canvas header. Disabled until "
            "the form is dirty (Name field typed). Clicking it opens "
            "discard_confirm_modal (ELITEA-2081)."
        ),
    )

    discard_confirm_modal = LocatorDescriptor(
        testid="toolkit-canvas-discard-confirm-modal",
        description="Discard confirmation modal (BaseModal) opened by discard_button.",
    )

    discard_confirm_button = LocatorDescriptor(
        testid="toolkit-canvas-discard-confirm-button",
        description="Discard button inside the confirmation modal.",
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

    def is_discard_enabled(self, timeout: int = 5000) -> bool:
        """Return True if the canvas header's Discard button is enabled (form is dirty)."""
        self.discard_button.wait_for(state="visible", timeout=timeout)
        return self.discard_button.is_enabled()

    @action("Click Discard on Toolkit canvas")
    def click_discard(self, timeout: int = 5000) -> None:
        """Click the canvas header's Discard button, opening the confirmation modal (ELITEA-2081)."""
        logger.info("Clicking Discard on Toolkit canvas")
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.click()
        self.discard_confirm_modal.wait_for(state="visible", timeout=timeout)

    @action("Confirm discard on Toolkit canvas")
    def confirm_discard(self, timeout: int = 5000) -> None:
        """Click Discard inside the confirmation modal and wait for it to close (ELITEA-2081)."""
        logger.info("Confirming discard on Toolkit canvas")
        self.discard_confirm_button.click()
        self.discard_confirm_modal.wait_for(state="detached", timeout=timeout)
