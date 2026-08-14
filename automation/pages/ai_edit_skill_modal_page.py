"""AI Edit Skill Modal Page - "Edit with AI" skill modification wizard.

Handles: ``AIEditSkillModal.jsx``, opened from the "Edit with AI" button in
the skill detail page's General section header (``/skills/all/{id}``).

The modal shell (prompt -> loading -> wizard) is ``EditEntityModal.jsx``,
shared with the Agent/Project-Context Edit-with-AI flows
(``entities/edit-entity-with-ai/``) — only the concrete testids and the
generate-draft endpoint differ per entity, mirroring the split already used
for "Build with AI" (``GenerateSkillModalPage`` vs
``GenerateEntityModalPageBase``). This page does NOT subclass
``GenerateEntityModalPageBase``: the Edit flow's post-generation UI is a
multi-step WIZARD (General -> Instructions -> Summary) with per-field
"Apply changes" checkboxes, materially different from Build's single
review-form step — the two page objects share no methods worth inheriting.

Wizard-phase testids (step indicator, checkboxes, nav buttons, Summary
inputs) were added via ``add-data-testid`` for ELITEA-2611
(EliteaAI/EliteaUI@cddfd6d4) — the wizard previously carried zero
data-testid wiring. The General step's Description CURRENT/SUGGESTED
column testids were added in fix round 1 (EliteaAI/EliteaUI@3e1e5c73) to
make Coverage Map rows 10/11 (read-only vs editable column display)
structurally assertable.

Covers: ELITEA-2611 (happy path — full wizard round-trip, partial apply via
per-field checkboxes, persistence across a full page reload); ELITEA-2612
(navigation/error handling — Refine Prompt preserves the prompt, Close
never applies uncommitted wizard state, a generation-failure error and
retry via the same Generate Draft control, empty/whitespace prompt
disable-only validation).
"""

import logging
import re

from playwright.sync_api import Page, Response, expect
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.ai_edit_skill_modal")


class AIEditSkillModalPage(BasePage):
    """Page object for the Skill "Edit with AI" modification wizard.

    Opened from the skill detail page (``/skills/all/{id}``); the modal
    itself is not tied to a URL.
    """

    GENERATE_DRAFT_ROUTE = "**/elitea_core/generate_skill_draft/**"

    # ------------------------------------------------------------------
    # Prompt phase — pre-existing testids (PROVENANCE: on-main, confirmed
    # live 2026-08-12, see AFS ELITEA-2611 Concrete Handles)
    # ------------------------------------------------------------------
    open_button = LocatorDescriptor(
        testid="edit-skill-with-ai-button",
        description='"Edit with AI" button, skill detail General section header',
    )
    modal = LocatorDescriptor(testid="ai-edit-skill-modal", description="Edit with AI modal container")
    close_button = LocatorDescriptor(testid="ai-edit-skill-close-button", description="Modal close (X) button")
    prompt_input = LocatorDescriptor(testid="ai-edit-skill-prompt-input", description="Prompt textarea")
    error_alert = LocatorDescriptor(
        testid="ai-edit-skill-error-alert", description="Generation-failure error alert"
    )
    loading_indicator = LocatorDescriptor(
        testid="ai-edit-skill-loading-indicator",
        description='"Generating skill draft..." loading state',
    )
    generate_button = LocatorDescriptor(
        testid="ai-edit-skill-generate-button", description='"Generate Draft" button'
    )
    cancel_button = LocatorDescriptor(
        testid="ai-edit-skill-cancel-button", description="Cancel button (prompt phase)"
    )

    # ------------------------------------------------------------------
    # Wizard phase — NEW testids, added for ELITEA-2611
    # ------------------------------------------------------------------
    step_indicator = LocatorDescriptor(
        testid="ai-edit-skill-step-indicator",
        description='Wizard step title text, e.g. "1. General" / "2. Instructions" / "3. Summary"',
    )
    refine_prompt_button = LocatorDescriptor(
        testid="ai-edit-skill-wizard-refine-prompt-button",
        description='Wizard footer — "Refine Prompt" (the wizard\'s ONLY '
                     "dismissal-to-prompt-phase control; there is no separate "
                     '"Back" button). Wired for ELITEA-2612 '
                     "(EliteaAI/EliteaUI@cbf9dd27) — the EditEntityModal prop "
                     "channel (refinePromptButtonTestId) already existed but was "
                     "left unwired at the call site until this case actually "
                     "clicked it (canon #511 executed-code-path rule).",
    )
    # NOTE: "Save as Version" wizard-footer button is NOT declared here. Its
    # EditEntityModal prop channel (saveAsVersionButtonTestId) exists but is
    # deliberately left unwired at the AIEditSkillModal.jsx call site — no
    # case yet clicks it, so the testid is not "referenced" per canon #511's
    # executed-code-path rule (no orphan testid is rendered). Add the field
    # here + wire the value in EliteaUI once a case actually exercises it.
    previous_button = LocatorDescriptor(
        testid="ai-edit-skill-wizard-previous-button",
        description="Wizard footer — Previous (hidden on the first visible step)",
    )
    next_button = LocatorDescriptor(
        testid="ai-edit-skill-wizard-next-button",
        description="Wizard footer — Next (hidden on the last step)",
    )
    wizard_save_button = LocatorDescriptor(
        testid="ai-edit-skill-wizard-save-button",
        description="Wizard footer, last step — Save. Distinct from the "
                     "prompt-phase generate_button and the form-level "
                     "SkillFormPage.save_button.",
    )
    general_name_checkbox = LocatorDescriptor(
        testid="ai-edit-skill-general-name-checkbox",
        description="General step — Name 'Apply changes' checkbox. Testid "
                     "lands on the MUI BaseCheckbox root span, not the "
                     "visually-hidden native <input> — read checked state "
                     "via the Mui-checked CSS class (see "
                     "_is_mui_checkbox_checked), same workaround as "
                     "admin_users_page.py's select_all_checkbox.",
    )
    general_description_checkbox = LocatorDescriptor(
        testid="ai-edit-skill-general-description-checkbox",
        description="General step — Description 'Apply changes' checkbox "
                     "(same Mui-checked class workaround)",
    )
    instructions_checkbox = LocatorDescriptor(
        testid="ai-edit-skill-instructions-checkbox",
        description="Instructions step — 'Apply changes' checkbox (same "
                     "Mui-checked class workaround)",
    )

    general_description_current = LocatorDescriptor(
        testid="ai-edit-skill-general-description-current",
        description="General step — Description CURRENT column (read-only "
                     "display of the original text; renders as a plain "
                     "<Typography>, never carries contenteditable). Added "
                     "for ELITEA-2611 fix round 1 (EliteaAI/EliteaUI@3e1e5c73) "
                     "to make Coverage Map row 10 assertable.",
    )
    general_description_suggested = LocatorDescriptor(
        testid="ai-edit-skill-general-description-suggested",
        description="General step — Description SUGGESTED column (editable "
                     "diff view; renders as a contenteditable <div>). Added "
                     "for ELITEA-2611 fix round 1 (EliteaAI/EliteaUI@3e1e5c73) "
                     "to make Coverage Map row 11 assertable.",
    )

    summary_name_input = LocatorDescriptor(
        testid="ai-edit-skill-summary-name-input",
        description="Summary step — merged Name field (current or "
                     "suggested, depending on the Name checkbox's state)",
    )
    summary_description_input = LocatorDescriptor(
        testid="ai-edit-skill-summary-description-input",
        description="Summary step — merged Description field",
    )
    summary_instructions_input = LocatorDescriptor(
        testid="ai-edit-skill-summary-instructions-input",
        description="Summary step — merged Instructions field",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    @action("Open Edit with AI modal")
    def open_modal(self, timeout: int = 5000):
        """Click the "Edit with AI" button and wait for the modal to open."""
        self.open_button.click()
        self.modal.wait_for(state="visible", timeout=timeout)
        logger.info("Edit with AI modal opened")

    # ------------------------------------------------------------------
    # Prompt phase
    # ------------------------------------------------------------------

    @action("Fill edit prompt")
    def fill_prompt(self, text: str):
        """Fill the prompt textarea. testid resolves to the native
        <textarea> (wired via inputProps), so a plain fill() correctly
        triggers React's onChange."""
        self.prompt_input.click()
        self.prompt_input.fill(text)
        logger.info("Filled edit prompt: %d characters", len(text))

    def get_prompt_value(self) -> str:
        return self.prompt_input.input_value()

    def is_generate_enabled(self) -> bool:
        return self.generate_button.is_enabled()

    @action("Click Generate Draft, capturing the request body and response")
    def click_generate_and_wait_for_response(self, timeout: int = 30000) -> tuple[Response, dict, str]:
        """Click "Generate Draft" and return the ``generate_skill_draft``
        response PLUS its own captured request body.

        Reads the request body via a temporary ``page.route()``
        interceptor (reading ``route.request.post_data_json`` inside the
        handler, then ``route.continue_()``) rather than
        ``response.request.post_data_json`` — same DECLARED IMPROVISATION
        already established in this codebase for the identical reason
        (interception reads the body BEFORE the request leaves the
        browser, unaffected by the post-hoc-read timing gap) — see
        ``SkillFormPage.save_and_wait_for_navigation_capturing_payload()``
        and ``SecretsPage``'s twin method.

        The response body is the AUTHORITATIVE source for the AFS's
        diff-differs assertions (steps 6/7 — "SUGGESTED text differs from
        CURRENT") — reading it directly is more robust and faithful to
        "did the AI actually produce different content" than reading
        rendered/highlighted DOM. The General/Instructions comparison
        content (``TextDiffHighlight.jsx``) deliberately carries no
        data-testid — see AFS Automation Hints § Diff-highlighting
        assertion — so this is the sanctioned data-level read, not a
        workaround.

        Also captures the loading indicator's text WHILE it is visible (the
        real LLM call takes ~5-20s live, ample window) — read afterward via
        the returned tuple's third element, since by the time this method
        returns the modal has already transitioned to the wizard and the
        indicator is gone.

        Real LLM call — no mock, no fixed sleep; ~5-20s observed live per
        the AFS.

        Returns:
            A ``(response, request_body, loading_text)`` tuple: the
            Playwright ``Response`` for the generate-draft call, its
            parsed JSON request body (``{user_description, skill_id,
            version_id}``), and the loading indicator's text captured
            while visible.
        """
        captured: dict = {}

        def _capture_post_body(route):
            if route.request.method == "POST":
                captured["post_data_json"] = route.request.post_data_json
            route.continue_()

        self.page.route(self.GENERATE_DRAFT_ROUTE, _capture_post_body)
        try:
            with self.page.expect_response(
                lambda r: "generate_skill_draft" in r.url, timeout=timeout
            ) as response_info:
                self.generate_button.click()
                self.wait_for_loading_visible(timeout=min(timeout, 5000))
                loading_text = self.get_loading_text()
            response = response_info.value
        finally:
            self.page.unroute(self.GENERATE_DRAFT_ROUTE, _capture_post_body)

        logger.info("generate_skill_draft response: %d %s", response.status, response.url)
        return response, captured.get("post_data_json"), loading_text

    def wait_for_loading_visible(self, timeout: int = 3000):
        """Wait for the "Generating skill draft..." loading state to appear."""
        self.loading_indicator.wait_for(state="visible", timeout=timeout)

    def wait_for_wizard_visible(self, timeout: int = 30000):
        """Wait for the wizard phase (step indicator) to render, confirming
        the modal transitioned from loading to the wizard."""
        self.step_indicator.wait_for(state="visible", timeout=timeout)

    def get_loading_text(self) -> str:
        return self.loading_indicator.text_content() or ""

    # ------------------------------------------------------------------
    # Wizard — step indicator
    # ------------------------------------------------------------------

    def get_step_indicator_text(self) -> str:
        """Return the wizard's current step title, e.g. "1. General"."""
        return (self.step_indicator.text_content() or "").strip()

    # ------------------------------------------------------------------
    # Wizard — General step Description CURRENT/SUGGESTED column checks
    # (Coverage Map rows 10/11 — read-only vs editable structural proof)
    # ------------------------------------------------------------------

    def get_general_description_current_text(self) -> str:
        """Return the CURRENT (read-only) column's rendered text for
        Description."""
        return (self.general_description_current.text_content() or "").strip()

    def is_general_description_current_editable(self) -> bool:
        """Row 10 — CURRENT must be read-only: the column renders as a
        plain ``<Typography>`` and never carries a ``contenteditable``
        attribute at all (``get_attribute`` returns ``None``, not
        ``"false"``)."""
        return self.general_description_current.get_attribute("contenteditable") is not None

    def is_general_description_suggested_editable(self) -> bool:
        """Row 11 — SUGGESTED must be editable: the column renders as a
        ``contenteditable`` ``<div>`` (``TextDiffHighlight.jsx``, editable
        branch)."""
        return self.general_description_suggested.get_attribute("contenteditable") == "true"

    # ------------------------------------------------------------------
    # Wizard — General/Instructions step checkboxes
    # ------------------------------------------------------------------

    def _is_mui_checkbox_checked(self, locator) -> bool:
        """Read a MUI BaseCheckbox's checked state via its Mui-checked CSS
        class.

        The testid lands on the root span (MUI spreads unrecognized props
        there, not onto the visually-hidden native <input>), so
        Playwright's ``is_checked()`` cannot be used directly on it — same
        workaround already established for ``admin_users_page.py``'s
        ``select_all_checkbox``/row checkboxes (same underlying
        BaseCheckbox component).
        """
        class_attr = locator.get_attribute("class") or ""
        return "Mui-checked" in class_attr

    def is_name_checkbox_checked(self) -> bool:
        return self._is_mui_checkbox_checked(self.general_name_checkbox)

    def is_description_checkbox_checked(self) -> bool:
        return self._is_mui_checkbox_checked(self.general_description_checkbox)

    def is_instructions_checkbox_checked(self) -> bool:
        return self._is_mui_checkbox_checked(self.instructions_checkbox)

    @action("Uncheck the Description 'Apply changes' checkbox")
    def uncheck_description_checkbox(self):
        """Uncheck the General step's Description checkbox (no-op if
        already unchecked).

        Waits on the ``Mui-checked`` class actually leaving the checkbox's
        root ``<span>`` (framework condition-wait) instead of a fixed
        sleep — same class-list technique as :meth:`_is_mui_checkbox_checked`,
        driven through Playwright's auto-retrying ``expect()`` rather than
        a one-shot read.
        """
        if self.is_description_checkbox_checked():
            self.general_description_checkbox.click()
            expect(self.general_description_checkbox).not_to_have_class(re.compile("Mui-checked"))
        logger.info("Description 'Apply changes' checkbox unchecked")

    # ------------------------------------------------------------------
    # Wizard — navigation
    # ------------------------------------------------------------------

    @action("Click wizard Next")
    def click_next(self, timeout: int = 5000):
        """Click Next and wait for the step indicator to actually change,
        rather than a fixed sleep — the step transition is a synchronous
        React state update (``EditEntityModal``'s ``activeStepIndex``), so
        the indicator's text is the real completion signal."""
        previous_step = self.get_step_indicator_text()
        self.next_button.click()
        expect(self.step_indicator).not_to_have_text(previous_step, timeout=timeout)

    @action("Click wizard Previous")
    def click_previous(self, timeout: int = 5000):
        """Click Previous and wait for the step indicator to change (same
        condition-wait as :meth:`click_next`)."""
        previous_step = self.get_step_indicator_text()
        self.previous_button.click()
        expect(self.step_indicator).not_to_have_text(previous_step, timeout=timeout)

    @action("Click wizard Refine Prompt")
    def click_refine_prompt(self, timeout: int = 5000):
        """Click "Refine Prompt" and wait for the modal to return to the
        prompt-input phase.

        Unlike :meth:`click_next`/:meth:`click_previous` (which move
        between WIZARD steps and wait on the step indicator's text
        changing), "Refine Prompt" exits the wizard phase entirely back to
        the prompt-input phase — so the correct completion signal is the
        prompt textarea becoming visible again, not a step-indicator
        change (the step indicator is unmounted once back in the prompt
        phase, per ``EditEntityModal.jsx``'s ``handleRefinePrompt``, which
        resets ``phase`` to ``PHASES.PROMPT``).
        """
        self.refine_prompt_button.click()
        self.prompt_input.wait_for(state="visible", timeout=timeout)
        logger.info("Refine Prompt clicked — modal returned to prompt-input phase")

    # ------------------------------------------------------------------
    # Wizard — Summary step reads
    # ------------------------------------------------------------------

    def get_summary_name(self) -> str:
        return self.summary_name_input.input_value()

    def get_summary_description(self) -> str:
        return self.summary_description_input.input_value()

    def get_summary_instructions(self) -> str:
        return self.summary_instructions_input.input_value()

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    @action("Save wizard changes and wait for the skill-update response")
    def click_save_and_wait_for_response(self, timeout: int = 15000) -> Response:
        """Click the wizard's final-step Save and return the skill-update
        response.

        Waits on ``PUT .../elitea_core/skill/prompt_lib/{projectId}/{skillId}``
        (``skillUpdate`` mutation, ``skillsApi.js:187-200``) — the singular
        "skill" path confirms Save (not Save-as-Version) mutates the
        current version in place; the substring check does not collide
        with the plural create-flow endpoint
        (``/elitea_core/skills/prompt_lib/``) since "skill/" with a
        trailing slash is not a substring of "skills/".
        """
        with self.page.expect_response(
            lambda r: "/elitea_core/skill/prompt_lib/" in r.url and r.request.method == "PUT",
            timeout=timeout,
        ) as response_info:
            self.wizard_save_button.click()
        response = response_info.value
        logger.info("skill update PUT response: %d", response.status)
        return response
