"""Agent Canvas Page — in-chat "+ Create New Agent" canvas panel (ELITEA-2166).

Handles the right-side panel opened from ``ChatPage``'s ``+`` menu -> Agents
-> "+ Create New Agent" (``ChatPage.open_create_new_agent_canvas()``).

The panel renders the SAME ``CreateAgentForm`` component as the standalone
``/agents/create`` page — ``AgentFormPage`` already owns the Name/Description/
Instructions fields and the Save button under those exact testids
(``agent-name-input`` / ``agent-description-input`` / ``agent-instructions-input``
/ ``agent-save-button``). Per ``.agents/testing.md`` § Locator policy ("a
data-testid should appear in exactly one file"), this page object does NOT
redeclare those fields — reuse ``AgentFormPage(page)`` on the same ``page``
for filling the form and clicking Save (see the test for the composition
pattern; ``test_agent_with_toolkit_chat.py`` already composes ``AgentPage``
+ ``ChatPage`` the same way).

This page object owns only the canvas-specific chrome that has no
``AgentFormPage`` equivalent: the close (X) button, the title/subtitle
heading, and the 5 accordion section headers.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

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
