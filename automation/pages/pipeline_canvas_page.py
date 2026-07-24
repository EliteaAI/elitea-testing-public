"""Pipeline Canvas Page — in-chat "+ Create New Pipeline" canvas panel (ELITEA-2078).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu ->
Pipelines -> "+ Create New Pipeline"
(``ChatPage.open_create_new_pipeline_canvas()``).

The panel renders the SAME ``CreateAgentForm`` component as the standalone
``/pipelines/create`` page (``entityType="pipeline"``, ``showInstructions=
False``) for the Name/Description fields — ``AgentFormPage`` already owns
``agent-name-input``/``agent-description-input`` under those exact
testids, reused as-is (composition on the same ``page``, same pattern
``agent_canvas_page.py`` already established for the sibling Agent
canvas). This page object does NOT redeclare those fields.

The canvas-header Save button carries a DIFFERENT testid in CREATE mode
(``pipeline-save-button``, ``CreateApplicationSaveButton.jsx``) than the
Agent canvas's own Save button (``agent-save-button``) — the shared
``BaseEditor``/``EditorHeader`` chrome renders whichever ``saveButton``
node the caller passes in, and ``PipelineEditor.jsx`` passes a
pipeline-specific testid in create mode. It is therefore declared here,
not reused from ``AgentFormPage``. Once the pipeline is saved (edit mode),
the Save button swaps to a different component (``SaveApplicationButton.
jsx``) that DOES reuse the shared ``agent-save-button`` testid (confirmed
live, ELITEA-2078) — callers asserting the post-save Save-button state use
``AgentFormPage(page).save_button`` (or ``PipelineFormPage``/
``PipelineDetailPage``, same shared testid) for that, not this page
object.

This page object owns only the canvas-specific chrome this case's own
steps touch: the create-mode Save button, the Flow editor tab, and the
Discard button + its confirmation dialog + confirm button. The Close (X)
button and the Configuration tab exist as testids
(``pipeline-canvas-close-button`` / ``pipeline-canvas-configuration-tab``)
but this case's steps never click them, so per the "touches = executed
code path" scope ruling (canon #511) they are intentionally NOT declared
as fields here.
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.pipeline_canvas")


class PipelineCanvasPage(BasePage):
    """Page object for the in-chat 'Create New Pipeline' canvas panel."""

    save_button = LocatorDescriptor(
        testid="pipeline-save-button",
        description=(
            "Canvas Save button in CREATE mode only "
            "(CreateApplicationSaveButton.jsx). Distinct from "
            "AgentFormPage.save_button's 'agent-save-button' — the shared "
            "editor chrome renders a caller-supplied Save button node, and "
            "PipelineEditor.jsx supplies this pipeline-specific testid for "
            "create mode. Not rendered post-save."
        ),
    )

    flow_editor_tab = LocatorDescriptor(
        testid="pipeline-canvas-flow-editor-tab",
        description="'Flow editor' tab in the canvas header tab bar (post-save only).",
    )

    discard_button = LocatorDescriptor(
        testid="pipeline-canvas-discard-button",
        description=(
            "Canvas-header Discard button. DISABLED while the flow-editor "
            "graph has no unsaved changes; ENABLED once a node is added/"
            "removed without saving (EditorHeader.jsx's "
            "disabled={!isFormDirty && !isYamlCodeDirty})."
        ),
    )

    discard_confirm_dialog = LocatorDescriptor(
        testid="pipeline-canvas-discard-confirm-dialog",
        description=(
            "Discard confirmation dialog ('Warning' / 'Are you sure you "
            "want to discard changes?' / Cancel / Discard). MUI forwards "
            "this data-testid to the Dialog's own root wrapper — an "
            "ancestor of the role=\"dialog\" Paper (confirmed live) — but "
            "still usable for reading the dialog's full visible text via "
            "text_content(), which picks up descendant text regardless of "
            "which exact node carries the testid."
        ),
    )

    discard_confirm_button = LocatorDescriptor(
        testid="pipeline-canvas-discard-confirm-button",
        description=(
            "Dialog's 'Discard' (confirm) button — a real, directly "
            "clickable element (BaseModal.jsx wires confirmButtonTestId "
            "straight onto the Button.BaseBtn), unaffected by the dialog "
            "root's ancestor-testid placement above."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    @action("Open Flow editor tab")
    def open_flow_editor_tab(self, timeout: int = 10000):
        """Click the canvas's 'Flow editor' tab."""
        logger.info("Opening Flow editor tab")
        self.flow_editor_tab.wait_for(state="visible", timeout=timeout)
        self.flow_editor_tab.click()

    def is_discard_enabled(self) -> bool:
        """Return True if the Discard button is enabled (unsaved changes present)."""
        return self.discard_button.is_enabled()

    @action("Click Discard button")
    def click_discard(self, timeout: int = 5000):
        """Click the canvas-header Discard button, opening the confirm dialog."""
        logger.info("Clicking canvas Discard button")
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.click()
        self.discard_confirm_dialog.wait_for(state="visible", timeout=timeout)

    def get_discard_dialog_text(self, timeout: int = 5000) -> str:
        """Return the discard confirmation dialog's full visible text."""
        self.discard_confirm_dialog.wait_for(state="visible", timeout=timeout)
        return self.discard_confirm_dialog.text_content() or ""

    @action("Confirm discard")
    def confirm_discard(self, timeout: int = 5000):
        """Click the dialog's 'Discard' (confirm) button."""
        logger.info("Confirming discard")
        self.discard_confirm_button.wait_for(state="visible", timeout=timeout)
        self.discard_confirm_button.click()
