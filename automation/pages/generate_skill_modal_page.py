"""Generate Skill Modal Page - "Build with AI" skill draft generation.

Handles: the GenerateSkillModal opened from the "Build with AI" button in
the General accordion section header on ``/skills/create``
(``GenerateEntityModal.jsx`` via ``GenerateSkillModal.jsx``).

Covers:
- Opening the modal and entering a natural-language prompt
- Simulating/mocking the generate-draft network call (failure and retry)
- Reading the failure error alert and the transient loading state
- Detecting the transition to the review-form step after a successful
  generation
- Reading/editing the review-form's Name/Description/Instructions fields
  (added for ELITEA-1990; no Welcome Message/conversation starters unlike
  the Agent review form — see ELITEA-2001 AFS Axis 2)

Shell behavior (loading -> error -> retry -> review) is shared with the
Agent "Build with AI" flow via ``GenerateEntityModalPageBase`` — see
``generate_agent_modal_page.py`` for the sibling entity page object.
"""

from playwright.sync_api import Page

from .generate_entity_modal_page_base import GenerateEntityModalPageBase
from .locator_descriptor import LocatorDescriptor


class GenerateSkillModalPage(GenerateEntityModalPageBase):
    """Page object for the "Build with AI" skill generation modal."""

    # The sole endpoint the modal calls to generate a draft
    # (GenerateSkillModal.jsx -> generateSkillDraftApi.js).
    GENERATE_DRAFT_ROUTE = "**/elitea_core/generate_skill_draft/**"

    open_button = LocatorDescriptor(
        testid="generate-skill-open-button",
        description='"Build with AI" button on the skill create form General section'
    )

    modal = LocatorDescriptor(
        testid="generate-skill-modal",
        description="Build with AI modal container"
    )

    close_button = LocatorDescriptor(
        testid="generate-skill-close-button",
        description="Modal close (X) button"
    )

    prompt_input = LocatorDescriptor(
        testid="generate-skill-prompt-input",
        description="Prompt textarea (input step)"
    )

    error_alert = LocatorDescriptor(
        testid="generate-skill-error-alert",
        description="Generation-failure error alert (input step)"
    )

    loading_indicator = LocatorDescriptor(
        testid="generate-skill-loading-indicator",
        description='"Generating skill draft..." loading state'
    )

    generate_button = LocatorDescriptor(
        testid="generate-skill-submit-button",
        description="Generate button — also the retry control (no separate retry affordance)"
    )

    cancel_button = LocatorDescriptor(
        testid="generate-skill-cancel-button",
        description="Cancel button (input step)"
    )

    back_button = LocatorDescriptor(
        testid="generate-skill-back-button",
        description="Back to prompt button (review step)"
    )

    approve_button = LocatorDescriptor(
        testid="generate-skill-approve-button",
        description="Create Skill button (review step)"
    )

    review_name_input = LocatorDescriptor(
        testid="generate-skill-review-name-input",
        description="Review-form Name field (editable before creation)",
    )

    review_description_input = LocatorDescriptor(
        testid="generate-skill-review-description-input",
        description="Review-form Description field (editable before creation)",
    )

    review_instructions_input = LocatorDescriptor(
        testid="generate-skill-review-instructions-input",
        description="Review-form Instructions field (editable before creation)",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_generate_draft_url(self, url: str) -> bool:
        return "generate_skill_draft" in url

    # ------------------------------------------------------------------
    # Review-form field access (Name / Description / Instructions)
    # ------------------------------------------------------------------

    def get_review_name(self) -> str:
        """Return the current value of the review-form Name field."""
        return self.review_name_input.input_value()

    def get_review_description(self) -> str:
        """Return the current value of the review-form Description field."""
        return self.review_description_input.input_value()

    def get_review_instructions(self) -> str:
        """Return the current value of the review-form Instructions field."""
        return self.review_instructions_input.input_value()

    def set_review_name(self, value: str):
        """Overwrite the review-form Name field with ``value``.

        The testid resolves to the native ``<input>`` (wired via MUI
        ``slotProps.htmlInput``, same mechanism as ``prompt_input``), so a
        plain ``fill()`` correctly triggers React's controlled-component
        ``onChange``.
        """
        self.review_name_input.click()
        self.review_name_input.fill(value)

    def set_review_description(self, value: str):
        """Overwrite the review-form Description field with ``value``."""
        self.review_description_input.click()
        self.review_description_input.fill(value)

    def set_review_instructions(self, value: str):
        """Overwrite the review-form Instructions field with ``value``."""
        self.review_instructions_input.click()
        self.review_instructions_input.fill(value)
