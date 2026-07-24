"""Toolkit Canvas Page — in-chat "+ Create New Toolkit" canvas panel
(ELITEA-2082/2083/2080).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu ->
Toolkits -> "+ Create New Toolkit" (``ChatPage.open_create_new_toolkit_canvas()``).

The panel renders the SAME ``ToolkitTypeSelector``/``ToolkitForm`` components
the standalone ``/toolkits/create`` wizard uses — ``ToolkitCreationPage``
already owns the type-picker (``type_search_input``, ``TOOLKIT_TYPE_CARD``)
and the configuration form fields (``name_input``, ``TOOLKIT_FIELD_INPUT``)
under those exact testids. Per ``.agents/testing.md`` § Locator policy ("a
data-testid should appear in exactly one file"), this page object does NOT
redeclare those fields — reuse ``ToolkitCreationPage(page)`` on the same
``page`` (same composition pattern ``AgentCanvasPage`` already established
for the sibling "Create New Agent" canvas, ELITEA-2166).

This page object owns only the canvas-specific chrome that has no
``ToolkitCreationPage`` equivalent: the close (X) button, the title, the
create-mode action button (a genuinely different component/testid from the
standalone wizard's own Save button — ``CreateToolkitButton.jsx`` vs
``CreateToolkitToolTabBar.jsx``), and the Discard button + its confirm
dialog (also a distinct threading from the standalone wizard's Cancel flow
— ``EditorHeader.jsx``'s shared ``Button.DiscardButton``, not
``CreateToolkitToolTabBar.jsx``'s own Cancel button).
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.toolkit_canvas")


class ToolkitCanvasPage(BasePage):
    """Page object for the in-chat 'Create New Toolkit' canvas panel."""

    close_button = LocatorDescriptor(
        testid="toolkit-canvas-close-button",
        description="X (close) button on the create-toolkit canvas panel header.",
    )

    title = LocatorDescriptor(
        testid="toolkit-canvas-title",
        description=(
            "Canvas heading. Reads 'New Toolkit' before a type is chosen, "
            "'New Artifact Toolkit' (etc.) once a type is selected, and the "
            "toolkit's own name (e.g. 'test1') once Create succeeds."
        ),
    )

    create_button = LocatorDescriptor(
        testid="toolkit-form-create-button",
        description=(
            "Create-mode action button (CreateToolkitButton.jsx). Live label "
            "'Create', not 'Save' (case-text-drift clarification #1011 — the "
            "case's own wording calls this 'Save'). Unmounts entirely once the "
            "toolkit persists (the canvas swaps in SaveToolkitButton.jsx, a "
            "separate, untested-by-this-family component) — its own "
            "to_have_count(0) is the testid-only proof of that transition."
        ),
    )

    discard_button = LocatorDescriptor(
        testid="toolkit-canvas-discard-button",
        description="Discard button in the canvas header (EditorHeader.jsx's shared DiscardButton).",
    )

    discard_confirm_dialog = LocatorDescriptor(
        testid="toolkit-canvas-discard-confirm-dialog",
        description="'Warning' confirmation dialog shown after clicking Discard.",
    )

    discard_confirm_button = LocatorDescriptor(
        testid="toolkit-canvas-discard-confirm-button",
        description="'Discard' (confirm) button inside the Discard confirmation dialog.",
    )

    success_toast_message = LocatorDescriptor(
        testid="toast-message",
        description=(
            "Shared toast component (Toast.jsx) — reused by 3+ other page "
            "objects, each under its own named field per convention "
            "(e.g. ArtifactsPage.success_toast_message)."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (title visible)."""
        self.title.wait_for(state="visible", timeout=timeout)
        logger.info("Toolkit canvas open")

    @action("Close toolkit canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing toolkit canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()

    @action("Click create-mode action button on toolkit canvas")
    def click_create(self, timeout: int = 10000):
        """Click the create-mode action button (live label 'Create')."""
        self.create_button.wait_for(state="visible", timeout=timeout)
        self.create_button.click()
        logger.info("Clicked toolkit canvas create button")

    @action("Discard toolkit canvas changes (two-click confirm flow)")
    def discard(self, timeout: int = 10000):
        """Click Discard, wait for the confirm dialog, then click Discard again.

        Two-click sequence, same shape as ``ToolkitCreationPage.cancel_creation()``:
        the canvas's own Discard button always opens a "Warning" dialog first.
        """
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.click()
        self.discard_confirm_dialog.wait_for(state="visible", timeout=timeout)
        self.discard_confirm_button.click()
        logger.info("Confirmed Discard via the Warning dialog's Discard button")

    def is_discard_enabled(self, timeout: int = 5000) -> bool:
        """Return whether the Discard button is currently visible and enabled."""
        self.discard_button.wait_for(state="visible", timeout=timeout)
        return self.discard_button.is_enabled()
