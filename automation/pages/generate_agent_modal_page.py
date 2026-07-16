"""Generate Agent Modal Page - "Build with AI" agent draft generation.

Handles: the GenerateAgentModal opened from the "Build with AI" button in
the General accordion section header on ``/agents/create``
(``GenerateEntityModal.jsx`` via ``GenerateAgentModal.jsx``).

Covers:
- Opening the modal and entering a natural-language prompt
- Simulating/mocking the generate-draft network call (failure and retry)
- Reading the failure error alert and the transient loading state
- Detecting the transition to the review-form step after a successful
  generation (review-form field-level locators are out of scope here —
  see ELITEA-1915 AFS Concrete Handles)
- Reading the review form's Suggested Resources section (per-category
  section presence, item name/description, selection state) — see
  ELITEA-1907 AFS Concrete Handles. This is agent-specific (the
  ``ResourceSuggestions``/``SuggestionItem`` component pair lives only
  under ``generate-agent-modal/``, not shared with Skill's Build with AI).

Shell behavior (loading -> error -> retry -> review) is shared with the
Skill "Build with AI" flow via ``GenerateEntityModalPageBase`` — see
``generate_skill_modal_page.py`` for the sibling entity page object.
"""

import logging

from playwright.sync_api import Locator, Page

from .generate_entity_modal_page_base import GenerateEntityModalPageBase
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.generate_agent_modal")


class GenerateAgentModalPage(GenerateEntityModalPageBase):
    """Page object for the "Build with AI" agent generation modal."""

    # The sole endpoint the modal calls to generate a draft
    # (GenerateAgentModal.jsx -> generateAgentDraftApi.js).
    GENERATE_DRAFT_ROUTE = "**/elitea_core/generate_application_draft/**"

    open_button = LocatorDescriptor(
        testid="generate-agent-open-button",
        description='"Build with AI" button on the agent create form General section'
    )

    modal = LocatorDescriptor(
        testid="generate-agent-modal",
        description="Build with AI modal container"
    )

    close_button = LocatorDescriptor(
        testid="generate-agent-close-button",
        description="Modal close (X) button"
    )

    prompt_input = LocatorDescriptor(
        testid="generate-agent-prompt-input",
        description="Prompt textarea (input step)"
    )

    error_alert = LocatorDescriptor(
        testid="generate-agent-error-alert",
        description="Generation-failure error alert (input step)"
    )

    loading_indicator = LocatorDescriptor(
        testid="generate-agent-loading-indicator",
        description='"Generating agent draft..." loading state'
    )

    generate_button = LocatorDescriptor(
        testid="generate-agent-submit-button",
        description="Generate button — also the retry control (no separate retry affordance)"
    )

    cancel_button = LocatorDescriptor(
        testid="generate-agent-cancel-button",
        description="Cancel button (input step)"
    )

    back_button = LocatorDescriptor(
        testid="generate-agent-back-button",
        description="Back to prompt button (review step)"
    )

    approve_button = LocatorDescriptor(
        testid="generate-agent-approve-button",
        description="Create Agent button (review step)"
    )

    # ------------------------------------------------------------------
    # Suggested Resources (review step) — dynamic testids templated per
    # entityType (and item id where applicable), per this project's
    # `{section}-{element}-{param}` dynamic-testid convention
    # (ResourceSuggestions.jsx / SuggestionItem.jsx — see ELITEA-1907
    # AFS Concrete Handles). Class-level constants only — never build
    # these inline in a method or in a test/spec file.
    # ------------------------------------------------------------------
    RESOURCE_SECTION = '[data-testid="generate-agent-resource-section-{}"]'
    RESOURCE_ITEM = '[data-testid="generate-agent-resource-item-{}-{}"]'
    RESOURCE_CHECKBOX = '[data-testid="generate-agent-resource-checkbox-{}-{}"]'
    RESOURCE_NAME = '[data-testid="generate-agent-resource-name-{}-{}"]'
    RESOURCE_DESCRIPTION = '[data-testid="generate-agent-resource-description-{}-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_generate_draft_url(self, url: str) -> bool:
        return "generate_application_draft" in url

    # ------------------------------------------------------------------
    # Suggested Resources — getters
    # ------------------------------------------------------------------

    def is_resource_section_visible(self, entity_type: str) -> bool:
        """Whether the titled `"Suggested {Category}:"` section for
        ``entity_type`` (e.g. ``"toolkit"``, ``"mcp"``, ``"pipeline"``,
        ``"agent"``, ``"skill"``) is rendered.

        ``ResourceSuggestions.jsx`` returns ``null`` (no section at all,
        not just hidden) when its ``items`` array is empty — so this is a
        presence check, not a visibility-toggle check.
        """
        return self.page.locator(self.RESOURCE_SECTION.format(entity_type)).count() > 0

    def get_resource_item(self, entity_type: str, item_id) -> Locator:
        """Locator for one suggestion card (`SuggestionItem.jsx`)."""
        return self.page.locator(self.RESOURCE_ITEM.format(entity_type, item_id))

    def get_resource_name_text(self, entity_type: str, item_id) -> str:
        """The suggestion card's name text."""
        return self.page.locator(
            self.RESOURCE_NAME.format(entity_type, item_id)
        ).text_content() or ""

    def resource_description_exists(self, entity_type: str, item_id) -> bool:
        """Whether the description text node exists in the DOM at all.

        `SuggestionItem.jsx`'s `showSecondary` conditional means an item
        with no description renders no description element whatsoever —
        not an empty one. Callers must check existence before reading text.
        """
        return self.page.locator(self.RESOURCE_DESCRIPTION.format(entity_type, item_id)).count() > 0

    def get_resource_description_text(self, entity_type: str, item_id) -> str:
        """The suggestion card's description text. Call
        `resource_description_exists()` first — the element may not exist.
        """
        return self.page.locator(
            self.RESOURCE_DESCRIPTION.format(entity_type, item_id)
        ).text_content() or ""

    def is_resource_checked(self, entity_type: str, item_id) -> bool:
        """Whether the suggestion card's checkbox is checked.

        The testid resolves to `BaseCheckbox`'s MUI root `<span>`; the
        actual `<input type="checkbox">` is a child of it.
        """
        checkbox = self.page.locator(self.RESOURCE_CHECKBOX.format(entity_type, item_id))
        return checkbox.locator("input").is_checked()

    # ------------------------------------------------------------------
    # Suggested Resources — selection (ELITEA-1909)
    # ------------------------------------------------------------------

    @action("Select suggested resource")
    def select_resource(self, entity_type: str, item_id):
        """Click a suggestion card's checkbox to select it (see
        ELITEA-1909 AFS Concrete Handles).

        Args:
            entity_type: ``"toolkit"``, ``"mcp"``, ``"pipeline"``, ``"agent"``, or ``"skill"``.
            item_id: The suggested item's id (as returned in the draft response).
        """
        self.page.locator(self.RESOURCE_CHECKBOX.format(entity_type, item_id)).click()
        logger.info("Selected suggested resource %s/%s", entity_type, item_id)

    # ------------------------------------------------------------------
    # Create Agent (review step -> created agent) — ELITEA-1909
    # ------------------------------------------------------------------

    @action("Click Create Agent")
    def click_approve_and_wait_for_creation(self, timeout: int = 15000):
        """Click "Create Agent" and wait for the three sequential network
        calls the review step fires: the base-agent create (POST), the
        selected-Toolkit association (PATCH .../tool/prompt_lib/...), and
        the selected-Agent association (PATCH .../application_relation/prompt_lib/...).

        Per the ELITEA-1909 AFS Automation Hints, the UI's auto-navigation
        to the created agent's detail page can otherwise race ahead of the
        association calls completing — waiting on all three responses
        explicitly (rather than relying on navigation timing) avoids that.

        Returns:
            tuple: ``(create_response, toolkit_patch_response, agent_relation_patch_response)``
        """
        with self.page.expect_response(
            lambda r: "/elitea_core/applications/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as create_info, self.page.expect_response(
            lambda r: "/elitea_core/tool/prompt_lib/" in r.url and r.request.method == "PATCH",
            timeout=timeout,
        ) as toolkit_patch_info, self.page.expect_response(
            lambda r: "/elitea_core/application_relation/prompt_lib/" in r.url and r.request.method == "PATCH",
            timeout=timeout,
        ) as relation_patch_info:
            self.approve_button.click()

        create_response = create_info.value
        toolkit_patch_response = toolkit_patch_info.value
        relation_patch_response = relation_patch_info.value
        logger.info(
            "Create Agent: create=%d toolkit-patch=%d agent-relation-patch=%d",
            create_response.status, toolkit_patch_response.status, relation_patch_response.status,
        )
        return create_response, toolkit_patch_response, relation_patch_response
