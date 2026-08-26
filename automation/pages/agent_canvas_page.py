"""Agent Canvas Page — in-chat agent canvas panel (ELITEA-2166, ELITEA-2089).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu -> Agents
-> "+ Create New Agent" (create mode, ELITEA-2166), and also the edit canvas
opened by clicking the pencil icon next to a participant in the PARTICIPANTS
panel (edit mode, ELITEA-2089).

The panel renders the SAME ``CreateAgentForm`` / ``AgentEditor`` component as
the standalone ``/agents/create`` and ``/agents/all/{id}`` pages —
``AgentFormPage`` already owns the Name/Description/Instructions fields and
the Save button under those exact testids. Per ``.agents/testing.md`` §
Locator policy ("a data-testid should appear in exactly one file"), this page
object does NOT redeclare those fields — reuse ``AgentFormPage(page)`` on the
same ``page`` for filling the form and clicking Save.

This page object owns only the canvas-specific chrome that has no
``AgentFormPage`` equivalent: the close (X) button, the title/subtitle
heading, the Discard button, and the 5 accordion section headers.

ELITEA-2089 — ``discard_button`` added (testid ``agent-discard-button`` wired
in ``EditorHeader.jsx`` via new ``discardButtonTestId`` prop, passed from
``AgentEditor.jsx`` at its call site — pushed to ``automation/testids``).
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.agent_canvas")


class AgentCanvasPage(BasePage):
    """Page object for the in-chat 'Create New Agent' canvas panel."""

    close_button = LocatorDescriptor(
        testid="agent-canvas-close-button",
        description="X (close) button on the create-agent canvas panel header.",
    )

    title = LocatorDescriptor(
        testid="agent-canvas-title",
        description=(
            "Canvas heading. Reads 'Create New Agent' before Save; the "
            "agent's own name (e.g. 'echo') once Save succeeds."
        ),
    )

    subtitle = LocatorDescriptor(
        testid="agent-canvas-subtitle",
        description=(
            "Canvas subtitle — the active version name (e.g. 'base'). Not "
            "rendered pre-save (no version exists until the agent is created)."
        ),
    )

    discard_button = LocatorDescriptor(
        testid="agent-discard-button",
        description=(
            "Discard button in the agent canvas header. Becomes enabled when "
            "the agent form is dirty (ELITEA-2089). Testid wired in "
            "EditorHeader.jsx via discardButtonTestId prop from AgentEditor.jsx."
        ),
    )

    # Accordion section headers — dynamic per key. Templated class-level
    # constant per .agents/testing.md's dynamic-testid convention (never an
    # inline f-string in a method body).
    SECTION_HEADER = '[data-testid="agent-canvas-section-{}"]'

    # The 5 section keys wired in BasicAccordion's per-item ``testId`` prop
    # (CreateAgentForm.jsx / InstructionsInput.jsx / WelcomeMessage.jsx /
    # ConversationStarters.jsx / ApplicationAdvanceSettings.jsx).
    SECTION_KEYS = (
        "general", "instructions", "welcome-message", "chat-starters", "advanced",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def get_section_header(self, key: str):
        """Return the Locator for the accordion header identified by *key*.

        Args:
            key: One of ``SECTION_KEYS``.
        """
        return self.page.locator(self.SECTION_HEADER.format(key))

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (title visible)."""
        self.title.wait_for(state="visible", timeout=timeout)
        logger.info("Agent canvas open")

    @action("Close agent canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing agent canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()
