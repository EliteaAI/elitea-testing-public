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

import json
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

    # The base-agent CREATE endpoint (GenerateAgentModal.jsx:227 ->
    # useApplicationCreateMutation / api/applications.js's `applicationCreate`
    # mutation). Added for ELITEA-1916. The SAME URL also serves the
    # Agents-list GET queries (`applicationList`/`totalApplications` in
    # applications.js) — mock_create_failure() below scopes its handler to
    # POST only (route.continue_() for everything else) so a GET while the
    # mock is installed passes through untouched.
    CREATE_APPLICATION_ROUTE = "**/elitea_core/applications/prompt_lib/**"

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

    # --- App-wide toast (Toast.jsx, src/components/Toast.jsx) — shared
    # component, testids pre-exist and need no EliteaUI change (same
    # component already used by AgentDetailPage.toast_alert/toast_message,
    # ChatPage.toast_alert/toast_message, PipelineDetailPage.toast_alert/
    # toast_message; ELITEA-1916 is the first Build-with-AI-flow case to
    # need it — the base-create failure path surfaces its error via this
    # toast, not an inline modal alert, unlike the generate-draft failure
    # path's `error_alert` above). ---
    toast_alert = LocatorDescriptor(
        testid="toast-alert",
        description="App-wide toast Alert root; carries data-severity (info/warning/error/success).",
    )
    toast_message = LocatorDescriptor(
        testid="toast-message",
        description="App-wide toast message text body.",
    )
    # Severity-scoped toast alert selector — testid identity + data-severity
    # state filter, the compliant shape for a state-dependent assertion
    # (mirrors AgentDetailPage.TOAST_ALERT_SEVERITY / ChatPage.TOAST_ALERT_SEVERITY).
    TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'

    # ------------------------------------------------------------------
    # Review-form field access (Name / Description / Instructions) —
    # mirrors GenerateSkillModalPage's review_name_input/review_description_
    # input/review_instructions_input trio (added for ELITEA-1999). Landed
    # here for ELITEA-1920's fix round: the field-population claim ("Name/
    # Description/Instructions... all pre-populated") previously had no
    # UI-level assertion anywhere in the suite for the Agent review form
    # (GenerateAgentReviewForm.jsx had zero data-testid on these fields —
    # see ELITEA-1907 AFS Concrete Handles, "testid needed").
    # ------------------------------------------------------------------
    review_name_input = LocatorDescriptor(
        testid="generate-agent-review-name-input",
        description="Review-form Name field (editable before creation)",
    )

    # Name field's client-side validation helper text — added for ELITEA-1913
    # (GenerateAgentReviewForm.jsx's Name field had zero data-testid on its
    # MUI FormHelperText element before this case; see the ELITEA-1913 AFS
    # Concrete Handles — threaded through Input.InputBase's new
    # `helperTextTestId` prop, same pattern as `tooltipTestId`/
    # `tooltipContentTestId` in that shared component).
    review_name_helper_text = LocatorDescriptor(
        testid="generate-agent-review-name-helper-text",
        description="Review-form Name field's validation helper text (e.g. \"Name must be 32 characters or less\")",
    )

    review_description_input = LocatorDescriptor(
        testid="generate-agent-review-description-input",
        description="Review-form Description field (editable before creation)",
    )

    review_instructions_input = LocatorDescriptor(
        testid="generate-agent-review-instructions-input",
        description="Review-form Instructions field (editable before creation)",
    )

    # Welcome Message field — added for ELITEA-1906 (GenerateAgentReviewForm.jsx
    # had ZERO data-testid on this field before; see the ELITEA-1906 AFS Concrete
    # Handles). Wired the identical way as Name/Description/Instructions above.
    review_welcome_message_input = LocatorDescriptor(
        testid="generate-agent-review-welcome-message-input",
        description="Review-form Welcome Message field (editable before creation)",
    )

    # "Chat starters:" section header — added for ELITEA-1906 (case Step 9
    # requires verifying the section header is visible; the header carried no
    # testid before this case).
    review_starters_header = LocatorDescriptor(
        testid="generate-agent-review-starters-header",
        description='"Chat starters:" section header (only rendered when conversation_starters is non-empty)',
    )

    # ------------------------------------------------------------------
    # Review-form Chat-starter inputs (dynamic, per index) — added for
    # ELITEA-1906. Per this project's dynamic-testid convention
    # (.agents/testing.md § Locator policy), a class-level template constant;
    # never build these inline in a method or in a test/spec file.
    # ------------------------------------------------------------------
    REVIEW_STARTER_INPUT = '[data-testid="generate-agent-review-starter-input-{}"]'

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
    # Prefix-match variant of RESOURCE_ITEM — added for ELITEA-1910, to count
    # every rendered card for a category regardless of item id (the cap-of-5
    # check has no single known id to target). Same class-level dynamic-testid
    # convention as the other RESOURCE_* templates (.agents/testing.md §
    # Locator policy) — `^=` prefix match on the shared
    # `generate-agent-resource-item-{entityType}-{id}` naming scheme.
    RESOURCE_ITEM_PREFIX = '[data-testid^="generate-agent-resource-item-{}-"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_generate_draft_url(self, url: str) -> bool:
        return "generate_application_draft" in url

    # ------------------------------------------------------------------
    # Review-form field access — getters (mirrors GenerateSkillModalPage)
    # ------------------------------------------------------------------

    def get_review_name(self) -> str:
        """Return the current value of the review-form Name field."""
        return self.review_name_input.input_value()

    def is_review_name_invalid(self) -> bool:
        """Whether the review-form Name field currently carries
        `aria-invalid="true"` (added for ELITEA-1913 — the 32-char maximum
        validation state)."""
        return self.review_name_input.get_attribute("aria-invalid") == "true"

    def review_name_helper_text_visible(self) -> bool:
        """Whether the Name field's validation helper text element is
        rendered at all (added for ELITEA-1913 — MUI's `FormHelperText`
        only mounts when `helperText` is truthy)."""
        return self.review_name_helper_text.count() > 0

    def get_review_name_helper_text(self) -> str:
        """Return the Name field's validation helper text content. Call
        `review_name_helper_text_visible()` first — the element may not
        exist (added for ELITEA-1913)."""
        return self.review_name_helper_text.text_content() or ""

    def get_review_description(self) -> str:
        """Return the current value of the review-form Description field."""
        return self.review_description_input.input_value()

    def get_review_instructions(self) -> str:
        """Return the current value of the review-form Instructions field."""
        return self.review_instructions_input.input_value()

    def get_review_welcome_message(self) -> str:
        """Return the current value of the review-form Welcome Message field."""
        return self.review_welcome_message_input.input_value()

    def get_review_starter(self, index: int) -> Locator:
        """Locator for the review-form Chat-starter input at ``index``
        (0-based, matching ``conversation_starters`` array order)."""
        return self.page.locator(self.REVIEW_STARTER_INPUT.format(index))

    def get_review_starter_value(self, index: int) -> str:
        """Return the current value of the Chat-starter input at ``index``."""
        return self.get_review_starter(index).input_value()

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

    def count_resource_items(self, entity_type: str) -> int:
        """Count every rendered suggestion card for ``entity_type``,
        regardless of item id (prefix match on ``RESOURCE_ITEM_PREFIX``).

        Added for ELITEA-1910 (Suggested Skills cap-of-5 check) — unlike
        ``get_resource_item``, which targets one known id, this counts the
        full rendered set to check against a category's expected maximum.
        """
        return self.page.locator(self.RESOURCE_ITEM_PREFIX.format(entity_type)).count()

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

    # ------------------------------------------------------------------
    # Create Agent (review step -> created agent) with a selected Skill —
    # ELITEA-1911. A distinct wait pair from click_approve_and_wait_for_creation()
    # above: a selected Skill fires GET + PATCH .../skill/prompt_lib/{project}/{id}
    # (fetchSkillDetails + updateSkillRelation, per skillsApi.js), not the
    # tool-PATCH / application_relation-PATCH pair the Toolkit/Agent flow fires.
    # See the ELITEA-1911 AFS Gap assertions #2.
    # ------------------------------------------------------------------

    @action("Click Create Agent (with selected Skill)")
    def click_approve_and_wait_for_skill_creation(self, timeout: int = 15000):
        """Click "Create Agent" and wait for the base-agent create (POST)
        plus the selected-Skill's association pair: a ``GET`` (fetches the
        skill's ``version_details.id`` needed as ``skill_version_id``) and
        the ``PATCH .../skill/prompt_lib/{project}/{skillId}`` that attaches
        it (``has_relation: true``).

        Same rationale as :meth:`click_approve_and_wait_for_creation`: the
        UI's auto-navigation to the created agent's detail page can race
        ahead of the association calls completing, so all three responses
        are awaited explicitly rather than relying on navigation timing.

        Returns:
            tuple: ``(create_response, skill_get_response, skill_patch_response)``
        """
        with self.page.expect_response(
            lambda r: "/elitea_core/applications/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as create_info, self.page.expect_response(
            lambda r: "/elitea_core/skill/prompt_lib/" in r.url and r.request.method == "GET",
            timeout=timeout,
        ) as skill_get_info, self.page.expect_response(
            lambda r: "/elitea_core/skill/prompt_lib/" in r.url and r.request.method == "PATCH",
            timeout=timeout,
        ) as skill_patch_info:
            self.approve_button.click()

        create_response = create_info.value
        skill_get_response = skill_get_info.value
        skill_patch_response = skill_patch_info.value
        logger.info(
            "Create Agent (with Skill): create=%d skill-get=%d skill-patch=%d",
            create_response.status, skill_get_response.status, skill_patch_response.status,
        )
        return create_response, skill_get_response, skill_patch_response

    # ------------------------------------------------------------------
    # Create Agent (review step -> created agent) with NO resources
    # selected — ELITEA-1914. A plain draft (no suggested resources
    # rendered at all — see the ELITEA-1914 AFS Test Steps) never fires
    # any toolkit/agent-relation or skill GET/PATCH call, so waiting on
    # them the way click_approve_and_wait_for_creation() /
    # click_approve_and_wait_for_skill_creation() do would hang
    # indefinitely (both enter every expect_response context manager in
    # one `with` block). This helper waits ONLY on the base-agent create
    # POST, matching the plain-approve flow's actual network contract.
    # ------------------------------------------------------------------

    @action("Click Create Agent (no resources)")
    def click_approve_and_wait_for_agent_created(self, timeout: int = 15000):
        """Click "Create Agent" and wait for the base-agent create (POST)
        only — the correct wait for a plain draft with no suggested
        resources selected (or none rendered at all), where no
        toolkit/agent-relation or skill GET/PATCH call ever fires.

        Returns:
            The base-agent create response.
        """
        with self.page.expect_response(
            lambda r: "/elitea_core/applications/prompt_lib/" in r.url and r.request.method == "POST",
            timeout=timeout,
        ) as create_info:
            self.approve_button.click()

        create_response = create_info.value
        logger.info("Create Agent (no resources): create=%d", create_response.status)
        return create_response

    # ------------------------------------------------------------------
    # Create Agent — response-only wait, for callers that need to make
    # interim assertions WHILE the request is in flight (ELITEA-1916).
    # Mirrors GenerateEntityModalPageBase.expect_generate_response(): the
    # `with` block only starts waiting on `__exit__`, so a caller can
    # click, then assert transient state (e.g. the "Creating..." label /
    # disabled state), all before the response is awaited.
    # ------------------------------------------------------------------

    def expect_create_response(self, timeout: int = 15000):
        """Context manager: yields Playwright's response-info handle for
        the base-agent CREATE call (POST .../applications/prompt_lib/{id}),
        resolved once the block exits.

        Usage::

            with modal.expect_create_response() as response_info:
                modal.approve_button.click()
                # interim assertions while the (possibly mocked/delayed)
                # request is in flight, e.g. the transient "Creating..."
                # button state
            response = response_info.value
        """
        return self.page.expect_response(
            lambda response: (
                "/elitea_core/applications/prompt_lib/" in response.url
                and response.request.method == "POST"
            ),
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Network mocking — create-application endpoint (ELITEA-1916)
    # ------------------------------------------------------------------

    def mock_create_failure(
        self,
        error_message: str,
        status: int = 500,
        delay_ms: int = 300,
    ):
        """Install a route mock that fails the base-agent CREATE call
        (POST .../applications/prompt_lib/{project_id}).

        Scoped to POST only — the same URL also serves the Agents-list GET
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

        self.page.route(self.CREATE_APPLICATION_ROUTE, handler)
        logger.info("Mocked create-application failure: status=%d error=%r", status, error_message)

    def clear_create_mock(self):
        """Remove any route mock on the create-application endpoint."""
        self.page.unroute(self.CREATE_APPLICATION_ROUTE)
        logger.info("Cleared create-application route mock")
