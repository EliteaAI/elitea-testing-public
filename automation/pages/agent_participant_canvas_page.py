"""Agent participant read-only settings canvas — ELITEA-2075.

Handles the in-chat canvas opened via the PARTICIPANTS panel's "View
settings" button on a public (no-edit-permission) agent participant
(``AgentEditor.jsx`` with ``viewMode=Public`` / ``isPublic=true``).

This is the SAME ``BaseEditor``/``EditorHeader`` chrome (title/subtitle/close
testids) as the in-chat "Create New Agent" canvas already covered by
``AgentCanvasPage`` (ELITEA-2166) — confirmed via source (``AgentEditor.jsx``
passes the identical ``titleTestId``/``subtitleTestId``/``closeButtonTestId``
regardless of create-vs-view mode). Per ``.claude/rules/page-objects.md``
("no duplicate methods/locators across page objects" — a testid should
appear in exactly one file), this class INHERITS those three locators plus
``wait_for_open()``/``close()`` from ``AgentCanvasPage`` rather than
redeclaring them, and adds only the elements specific to the read-only
participant-settings view: the "Public" label, the TOOLS module toggles, and
the Model Settings dialog's Capabilities section / Apply button / Reasoning
slider per-level marks.

The Instructions field (read-only in this view) reuses the EXISTING
``agent-instructions-input`` testid via ``AgentFormPage.instructions_input``
(composition, not redeclaration — same shared ``FileReaderEnhancer``
rendering, just ``disabled=True`` here) — see the class docstring note below.
The LLM model selector / model settings dialog fields (``model-selector-*``/
``model-settings-*``) are likewise reused directly from ``AgentDetailPage``
by composition (same shared ``LLMModelSelector.jsx``/``LLMSettingsDialog.jsx``
widget tree) — see the test for the composition pattern, mirroring
``test_agent_with_toolkit_chat.py``'s existing ``AgentPage`` + ``ChatPage``
composition.

URL: /chat?edited_participant_id={id} (rendered inside the chat layout, not
a separate route)
"""

import logging

from playwright.sync_api import Page

from .agent_canvas_page import AgentCanvasPage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.agent_participant_canvas")


class AgentParticipantCanvasPage(AgentCanvasPage):
    """Read-only agent-participant settings canvas (View settings, public agent).

    Inherits ``title``/``subtitle``/``close_button``/``wait_for_open()``/
    ``close()`` from ``AgentCanvasPage`` (same ``EditorHeader`` chrome).
    """

    public_label = LocatorDescriptor(
        testid="agent-canvas-public-label",
        description=(
            "'Public' label shown in the canvas header instead of Discard/"
            "Save buttons, when the canvas is read-only (EditorHeader.jsx's "
            "isPublic branch)."
        ),
    )

    # TOOLS section module toggle switches — dynamic per module key (e.g.
    # "attachments", "data_analysis", "image_creation", "agents_pipeline").
    # Templated class-level constant per .agents/testing.md's dynamic-testid
    # convention — never an inline f-string in a method body.
    TOOLS_TOGGLE = '[data-testid="agent-canvas-tools-toggle-{}"]'
    # Prefix-match enumerating every currently-rendered module toggle,
    # regardless of module key — used to count how many are visible without
    # hardcoding the internal-tools name list (which is itself
    # toolkit-availability-dependent — useAvailableInternalTools.hooks.js).
    TOOLS_TOGGLE_PREFIX = '[data-testid^="agent-canvas-tools-toggle-"]'

    # --- Model Settings dialog additions (shared LLMSettingsDialog.jsx
    # widget tree — the dialog container/Cancel/reasoning-slider-container/
    # max-tokens-section testids themselves are reused from AgentDetailPage
    # by composition, not redeclared here). ---

    model_settings_capabilities_section = LocatorDescriptor(
        testid="model-settings-capabilities-section",
        description=(
            "Capabilities section inside the Model settings dialog "
            "(CapabilitySection.jsx) — shows 'Image analysis'/'Reasoning' "
            "chips for the selected model. Conditionally rendered (returns "
            "null when the model supports neither)."
        ),
    )

    model_settings_apply_button = LocatorDescriptor(
        testid="model-settings-apply-button",
        description="Apply button in the Model settings dialog (LLMSettingsDialog.jsx).",
    )

    # Reasoning slider's per-level invisible click-trigger Box — dynamic per
    # numeric slider position (1=Low, 2=Medium, 3=High). Replaces the
    # bounding-box-relative click the AFS originally proposed (brittle,
    # non-testid) now that a real handle exists (DiscreteSlider.jsx's
    # markTestIdPrefix, threaded from ReasoningSlider.jsx).
    REASONING_LEVEL_MARK = '[data-testid="model-settings-reasoning-level-{}"]'
    REASONING_LEVEL_HIGH = 3

    def __init__(self, page: Page):
        super().__init__(page)

    def get_tools_toggle(self, module_key: str):
        """Return the Locator for the TOOLS module toggle identified by *module_key*."""
        return self.page.locator(self.TOOLS_TOGGLE.format(module_key))

    def get_all_tools_toggles(self, timeout: int = 10000):
        """Return the Locator matching every currently-rendered module toggle.

        Waits for the first toggle to be attached before returning — the
        TOOLS section's toggle list depends on ``useGetCurrentToolkitSchemas``
        resolving, which can lag the canvas's own initial render.
        """
        toggles = self.page.locator(self.TOOLS_TOGGLE_PREFIX)
        toggles.first.wait_for(state="attached", timeout=timeout)
        return toggles

    def is_tools_toggle_checked(self, module_key: str) -> bool:
        """Return the toggle's ``checked`` DOM property (NOT the ``disabled``/
        ``aria-disabled`` attributes, which this component does not set —
        AFS § Concrete Handles)."""
        return self.get_tools_toggle(module_key).is_checked()

    @action("Select Reasoning level")
    def select_reasoning_level(self, level: int, timeout: int = 5000):
        """Click the Reasoning slider's per-level mark (1=Low, 2=Medium, 3=High)."""
        mark = self.page.locator(self.REASONING_LEVEL_MARK.format(level))
        mark.wait_for(state="visible", timeout=timeout)
        mark.click()

    @action("Apply Model settings")
    def click_apply_settings(self):
        """Click Apply in the Model settings dialog.

        Does not itself wait for the dialog to close — that testid
        (``model-settings-dialog``) belongs to ``AgentDetailPage`` (reused by
        composition, not redeclared here per the class docstring); callers
        wait on their own composed ``AgentDetailPage`` instance's
        ``model_settings_dialog.wait_for(state="hidden")``.
        """
        self.model_settings_apply_button.click()
