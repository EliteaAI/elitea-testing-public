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

Also covers (ELITEA-2000): a CREATE-time failure (mocked 500 on the
base-create POST, not the generate-draft call) surfaces an app-wide toast
(``toast_alert``/``toast_message``), leaves the review form open with the
draft intact, and a retry via the same "Create Skill" button succeeds once
the mock is cleared — see ``mock_create_failure()``,
``expect_create_response()``, ``click_approve_and_wait_for_creation()``
below (added mirroring ``generate_agent_modal_page.py``'s ELITEA-1916
additions).
"""

import json
import logging

from playwright.sync_api import Page
from utils.actions import action

from .generate_entity_modal_page_base import GenerateEntityModalPageBase
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.generate_skill_modal")


class GenerateSkillModalPage(GenerateEntityModalPageBase):
    """Page object for the "Build with AI" skill generation modal."""

    # The sole endpoint the modal calls to generate a draft
    # (GenerateSkillModal.jsx -> generateSkillDraftApi.js).
    GENERATE_DRAFT_ROUTE = "**/elitea_core/generate_skill_draft/**"

    # The base-skill CREATE endpoint (GenerateSkillModal.jsx ->
    # useSkillCreateMutation / skillsApi.js's `skillCreate` mutation ->
    # POST /elitea_core/skills/prompt_lib/{project_id}). Added for
    # ELITEA-2000. The SAME URL also serves the Skills-list GET queries
    # (`skillList`/`totalSkills` in skillsApi.js) — mock_create_failure()
    # below scopes its handler to POST only (route.continue_() for
    # everything else) so a GET while the mock is installed passes through
    # untouched.
    CREATE_SKILL_ROUTE = "**/elitea_core/skills/prompt_lib/**"

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

    review_name_helper_text = LocatorDescriptor(
        testid="generate-skill-review-name-helper-text",
        description="Review-form Name field's validation/character-count helper text "
                     "(added for ELITEA-1993)",
    )

    # --- App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared
    # component already used by AgentDetailPage.toast_alert/toast_message,
    # GenerateAgentModalPage.toast_alert/toast_message (ELITEA-1916),
    # ChatPage.toast_alert/toast_message, PipelineDetailPage.toast_alert/
    # toast_message; ELITEA-2000 is the first Skill Build-with-AI-flow case
    # to need it — the CREATE-time failure surfaces via this app-wide
    # toast, not an inline modal alert, unlike the generate-draft failure
    # path (which uses ``error_alert`` above).
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )
    # Severity-scoped toast alert selector — testid identity + data-severity
    # state filter, per the testid-only locator policy's state-via-attribute
    # rule (mirrors GenerateAgentModalPage.TOAST_ALERT_SEVERITY).
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

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

    def get_review_name_helper_text(self) -> str:
        """Return the review-form Name field's current helper text (a
        validation error message, or the plain '{len}/64' character-count
        counter when the value is valid)."""
        return self.review_name_helper_text.text_content() or ""

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

    # ------------------------------------------------------------------
    # Create Skill (review step -> created skill) — ELITEA-2000. Mirrors
    # GenerateAgentModalPage's expect_create_response() (ELITEA-1916), but
    # the Skill entity's create response wait is simpler: no suggested-
    # resources concept exists on a Skill draft, so no follow-up
    # toolkit/agent-relation/skill association call ever fires (unlike the
    # Agent entity's click_approve_and_wait_for_creation() variants) — a
    # single-response wait on the base-skill create POST is the correct
    # and complete pattern here.
    # ------------------------------------------------------------------

    def expect_create_response(self, timeout: int = 15000):
        """Context manager: yields Playwright's response-info handle for
        the base-skill CREATE call (POST .../skills/prompt_lib/{id}),
        resolved once the block exits.

        Usage::

            with modal.expect_create_response() as response_info:
                modal.approve_button.click()
                # interim assertions while the (possibly mocked/delayed)
                # request is in flight
            response = response_info.value
        """
        return self.page.expect_response(
            lambda response: (
                "/elitea_core/skills/prompt_lib/" in response.url
                and response.request.method == "POST"
            ),
            timeout=timeout,
        )

    @action("Click Create Skill")
    def click_approve_and_wait_for_creation(self, timeout: int = 15000):
        """Click "Create Skill" and wait for the base-skill create (POST)
        response only — the correct and complete wait for this entity,
        since no suggested-resources association call ever follows a
        Skill create (see class docstring).

        Returns:
            The base-skill create response.
        """
        with self.page.expect_response(
            lambda r: "/elitea_core/skills/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as create_info:
            self.approve_button.click()

        create_response = create_info.value
        logger.info("Create Skill: create=%d", create_response.status)
        return create_response

    # ------------------------------------------------------------------
    # Network mocking — create-skill endpoint (ELITEA-2000)
    # ------------------------------------------------------------------

    def mock_create_failure(
        self,
        error_message: str,
        status: int = 500,
        delay_ms: int = 300,
    ):
        """Install a route mock that fails the base-skill CREATE call
        (POST .../skills/prompt_lib/{project_id}).

        Scoped to POST only — the same URL also serves the Skills-list GET
        queries, which are passed through via ``route.continue_()``.

        Args:
            error_message: Body ``error`` field — surfaced verbatim by
                ``GenerateEntityModal.jsx``'s ``handleApprove`` catch block
                (``toastError(buildErrorMessage(err))``), via an app-wide
                toast (NOT the inline ``error_alert`` the generate-draft
                failure path uses).
            status: HTTP status to fulfill with.
            delay_ms: Artificial latency before fulfilling, so the transient
                "Creating..." (``isApproving``) state is reliably observable.
        """
        def handler(route):
            if route.request.method != "POST":
                route.continue_()
                return
            self.page.wait_for_timeout(delay_ms)
            route.fulfill(
                status=status,
                content_type="application/json",
                body=json.dumps({"error": error_message}),
            )

        self.page.route(self.CREATE_SKILL_ROUTE, handler)
        logger.info("Mocked create-skill failure: status=%d error=%r", status, error_message)

    def clear_create_mock(self):
        """Remove any route mock on the create-skill endpoint."""
        self.page.unroute(self.CREATE_SKILL_ROUTE)
        logger.info("Cleared create-skill route mock")
