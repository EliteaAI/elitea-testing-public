"""Project Context Chat Canvas Page — in-chat Project Context editor chrome
opened from a ``generated-entity-chip`` click (ELITEA-3368).

Handles the right-side panel opened when ``ChatPage.open_generated_entity_chip()``
is used on a "Project Context" chip. The panel renders the SAME
``ProjectContextEditor``/``BaseEditor`` chrome as every other in-chat
create-via-chat canvas (Agent/Pipeline/MCP) — confirmed live via full source
read (``EliteaUI/src/[fsd]/features/chat/ui/editors/ProjectContextEditor.jsx``
wraps ``@/[fsd]/features/settings/ui/project-context``'s ``ProjectContextEditor``
feature component with ``inlineMode`` on the SAME ``BaseEditor`` chrome every
other canvas uses) — and the editor's own CONTENT reuses
``ProjectContextPage``'s existing testids verbatim
(``project-context-editor-content`` / ``project-context-save-button`` /
``project-context-char-counter``, all from ELITEA-2272). Per
``.agents/testing.md`` § Locator policy ("a data-testid should appear in
exactly one file"), this page object does NOT redeclare those fields — compose
``ProjectContextPage(page)`` on the SAME ``page``, mirroring the
``McpCanvasPage`` + ``McpFormPage`` composition pattern.

This page object owns only the canvas-specific chrome that has no
``ProjectContextPage`` equivalent: the close (X) button. Confirmed live +
via source: ``ProjectContextEditor.jsx``'s (chat variant) ``<BaseEditor
title="Project Context">`` call passes neither ``titleTestId`` nor
``closeButtonTestId`` (both props exist end-to-end on
``BaseEditor``/``EditorHeader``, same omitted-optional-prop gap
``mcp-canvas-title``/``agent-canvas-close-button`` had before their own
fixes) — so both the heading and the close button are declared on the
ladder here (role/css rungs with ``suggested_testid=``), not testid.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.project_context_chat_canvas")


class ProjectContextChatCanvasPage(BasePage):
    """Page object for the in-chat Project Context editor canvas's chrome."""

    # Both declarations below are scoped off the SAME unique anchor —
    # editor_content's nearest ancestor <form> (BaseEditor's Formik
    # <Form>, which wraps exactly ONE EditorHeader + ONE content Box per
    # open canvas — confirmed via BaseEditor.jsx source read). No numeric
    # index anywhere (XPath predicates are text/class-based only), so
    # neither declaration is positional.
    title = LocatorDescriptor(
        xpath=(
            '//*[@data-testid="project-context-editor-content"]'
            '/ancestor::form'
            '//*[contains(@class, "MuiTypography")]'
            '[normalize-space(text())="Project Context"]'
        ),
        suggested_testid="project-context-canvas-title",
        description=(
            "Canvas heading Typography (EditorHeader.jsx). No data-testid "
            "on this build — ProjectContextEditor.jsx's chat-canvas call "
            "site passes BaseEditor no titleTestId (same omitted-prop gap "
            "mcp-canvas-title/agent-canvas-title had before their own "
            "add-data-testid fixes). Scoped to a MuiTypography element "
            "with the exact literal text so it can never match the "
            "CodeMirror editor body below it (a different, non-Typography "
            "DOM subtree) even if AI-generated content happened to "
            "contain the same words."
        ),
    )

    close_button = LocatorDescriptor(
        xpath=(
            '//*[@data-testid="project-context-editor-content"]'
            '/ancestor::form'
            '//*[contains(@class, "MuiTypography")]'
            '[normalize-space(text())="Project Context"]'
            '/parent::*/preceding-sibling::button'
        ),
        suggested_testid="project-context-canvas-close-button",
        description=(
            "X (close) button on the Project Context canvas header "
            "(EditorHeader.jsx's close IconButton — no aria-label, no "
            "testid on this build, confirmed via full source read: "
            "ProjectContextEditor.jsx's chat-canvas call site never "
            "passes closeButtonTestId). EditorHeader.jsx's own structure "
            "(confirmed via source) renders the close IconButton as a "
            "DIRECT preceding-sibling of the Box wrapping the title "
            "Typography inside the same titleSection container — this "
            "declaration walks that exact, non-positional structural "
            "relationship (title's text -> its parent Box -> that Box's "
            "preceding button sibling) rather than picking by index or "
            "page-wide coordinate. The ONLY other icon-only buttons on "
            "this canvas (Import/Copy, ProjectContextEditor.jsx feature "
            "toolbar) live in a sibling content Box entirely outside "
            "EditorHeader's titleSection, so they can never match this "
            "declaration's preceding-sibling path."
        ),
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_for_open(self, timeout: int = 10000):
        """Wait until the canvas panel has rendered (title text visible)."""
        self.title.wait_for(state="visible", timeout=timeout)
        logger.info("Project Context chat canvas open")

    @action("Close Project Context chat canvas")
    def close(self, timeout: int = 5000):
        """Click the canvas's X (close) button."""
        logger.info("Closing Project Context chat canvas")
        self.close_button.wait_for(state="visible", timeout=timeout)
        self.close_button.click()
