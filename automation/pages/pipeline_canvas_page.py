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
``PipelineDetailPage`` equivalent: the close (X) button and the post-save
Configuration/Flow editor tab bar.
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
