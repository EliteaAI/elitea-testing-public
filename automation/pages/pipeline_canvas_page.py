"""Pipeline Canvas Page — in-chat "+ Create New Pipeline" canvas panel (ELITEA-2079).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu ->
Pipelines -> "+ Create New Pipeline"
(``ChatPage.open_create_new_pipeline_canvas()``).

The panel renders the SAME ``CreateAgentForm`` component (entityType=
"pipeline") as the standalone ``/pipelines/create`` page for the create-mode
Name/Description fields and Save button, and the SAME ``EditorPanel``
component as the standalone ``/pipelines/all/{id}`` page for the Flow
Editor/YAML internals once the pipeline is created — ``PipelineFormPage``/
``PipelineDetailPage`` already own those testids
(``agent-name-input``/``agent-description-input``/``agent-save-button``,
``pipeline-flow-view``/``pipeline-yaml-view``/``pipeline-yaml-editor``, the
ReactFlow canvas). Per ``.agents/testing.md`` § Locator policy ("a
data-testid should appear in exactly one file"), this page object does NOT
redeclare those fields — reuse ``PipelineDetailPage(page)`` on the same
``page`` for form filling, Save, and Flow Editor operations (same
composition pattern as ``AgentCanvasPage`` + ``AgentFormPage`` in
``test_create_agent_via_chat_canvas.py``).

This page object owns only the canvas-specific chrome that has no
``PipelineDetailPage`` equivalent: the close (X) button, the post-save
Configuration/Flow editor tab bar, and the create-mode Discard button +
its confirmation modal (ELITEA-2076).

ELITEA-2076 — ``discard_button``/``discard_confirm_modal``/
``discard_confirm_button`` added. ``BaseEditor.jsx``/``EditorHeader.jsx``
already rendered a Discard button (via the pre-existing
``discardButtonTestId`` prop, ELITEA-2089) and its confirmation modal
(``Button.DiscardButton`` unconditionally opens one before calling the
caller's ``onDiscard`` — same mechanism ``ToolkitCreationPage`` already
drives), but neither the modal nor its confirm button had a testid path
threaded through — only ``CredentialsTabBar.jsx`` called
``Button.DiscardButton`` directly with ``modalDataTestId``/
``confirmButtonDataTestId``. Added two new optional props,
``discardModalTestId``/``discardConfirmButtonTestId``, through
``BaseEditor.jsx`` -> ``EditorHeader.jsx`` -> the existing
``Button.DiscardButton`` props (same shape as the pre-existing
``discardButtonTestId``), supplied ONLY at ``PipelineEditor.jsx``'s call
site (``pipeline-canvas-discard-button``,
``pipeline-canvas-discard-confirm-modal``,
``pipeline-canvas-discard-confirm-button``) — the sibling Agent/MCP chat
canvases (``AgentEditor.jsx``/``ToolkitEditor.jsx``) are unaffected since
the new props are optional and caller-supplied
(``.agents/testing.md`` § "Shared components never hardcode
feature-scoped testids").
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.pipeline_canvas")


class PipelineCanvasPage(BasePage):
    """Page object for the in-chat 'Create New Pipeline' canvas panel."""

    close_button = LocatorDescriptor(
        testid="pipeline-canvas-close-button",
        description=(
            "X (close) button on the pipeline canvas panel header — "
            "threaded as BaseEditor/EditorHeader's optional "
            "closeButtonTestId prop, same shape as "
            "AgentCanvasPage.close_button (ELITEA-2079 add-data-testid)."
        ),
    )

    configuration_tab = LocatorDescriptor(
        testid="pipeline-canvas-tab-configuration",
        description=(
            "'Configuration' tab in the post-save canvas tab bar "
            "(PipelineEditor.jsx's own Tabs, distinct from the standalone "
            "detail page's pipeline-config-tab)."
        ),
    )

    flow_editor_tab = LocatorDescriptor(
        testid="pipeline-canvas-tab-flow",
        description=(
            "'Flow editor' tab in the post-save canvas tab bar — clicking "
            "it reveals the same EditorPanel PipelineDetailPage drives "
            "standalone."
        ),
    )

    discard_button = LocatorDescriptor(
        testid="pipeline-canvas-discard-button",
        description=(
            "Discard button in the pipeline canvas header. Disabled until "
            "the form is dirty (Name/Description typed). Clicking it opens "
            "discard_confirm_modal (ELITEA-2076)."
        ),
    )

    discard_confirm_modal = LocatorDescriptor(
        testid="pipeline-canvas-discard-confirm-modal",
        description="Discard confirmation modal (BaseModal) opened by discard_button.",
    )

    discard_confirm_button = LocatorDescriptor(
        testid="pipeline-canvas-discard-confirm-button",
        description="Discard button inside the confirmation modal.",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (close button visible)."""
        self.close_button.wait_for(state="visible", timeout=timeout)
        logger.info("Pipeline canvas open")

    @action("Close pipeline canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing pipeline canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()

    @action("Click Flow editor tab")
    def click_flow_editor_tab(self, timeout: int = 10000):
        """Click the post-save canvas's 'Flow editor' tab."""
        logger.info("Clicking Flow editor tab")
        self.flow_editor_tab.wait_for(state="visible", timeout=timeout)
        self.flow_editor_tab.click()

    def is_discard_enabled(self, timeout: int = 5000) -> bool:
        """Return True if the canvas header's Discard button is enabled (form is dirty)."""
        self.discard_button.wait_for(state="visible", timeout=timeout)
        return self.discard_button.is_enabled()

    @action("Click Discard on pipeline canvas")
    def click_discard(self, timeout: int = 5000) -> None:
        """Click the canvas header's Discard button, opening the confirmation modal (ELITEA-2076)."""
        logger.info("Clicking Discard on pipeline canvas")
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.click()
        self.discard_confirm_modal.wait_for(state="visible", timeout=timeout)

    @action("Confirm discard on pipeline canvas")
    def confirm_discard(self, timeout: int = 5000) -> None:
        """Click Discard inside the confirmation modal and wait for it to close (ELITEA-2076)."""
        logger.info("Confirming discard on pipeline canvas")
        self.discard_confirm_button.click()
        self.discard_confirm_modal.wait_for(state="detached", timeout=timeout)
