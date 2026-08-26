"""Generate Project Context Modal Page — "Build with AI" on Settings → Project Context.

Handles the ``GenerateProjectContextModal`` opened either from the Project
Context **empty state**'s "Build with AI" button (which navigates to
``/settings/project-context/edit`` and auto-opens the dialog) or from the
**editor toolbar**'s "Build with AI" button.

Third subclass of :class:`GenerateEntityModalPageBase`, alongside
``GenerateAgentModalPage`` and ``GenerateSkillModalPage``: all three render the
same shared ``GenerateEntityModal.jsx`` shell (INPUT → LOADING → REVIEW), so
only the testid naming convention, the review-form fields and the
generate-draft endpoint differ.

Locator provenance (ELITEA-2269 — seven testids added to ``EliteaAI/EliteaUI``
``automation/testids``, EliteaAI/EliteaUI@d6eb52b6). **The shared components
were not modified**: every modal testid rides a prop ``GenerateEntityModal`` /
``GenerateEntityButton`` already accepted and that project context simply left
``undefined`` (``modalTestId``, ``promptInputTestId``,
``loadingIndicatorTestId``, ``generateButtonTestId``, ``cancelButtonTestId``,
``approveButtonTestId``, ``buttonTestId``). The review form's Project
Background field carries a plain ``data-testid`` threaded through MUI's
``slotProps.htmlInput`` so it lands on the real ``<textarea>`` — ``input_value()``
reads the draft directly rather than off a wrapper.

The empty state's own "Build with AI" button
(``project-context-build-with-ai-button``) belongs to the page, not to this
dialog, and lives on :class:`~pages.project_context_page.ProjectContextPage`.

Toolbar-swap note (ELITEA-2270, clarification #1797): the editor renders
"Build with AI" ONLY while the content is empty — one character of content and
``ProjectContextEditor.jsx`` swaps it for "Edit with AI"
(``ai-edit-project-context-open-button``, a different dialog). So
:attr:`open_button` is reachable on an untouched editor only.
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .generate_entity_modal_page_base import GenerateEntityModalPageBase
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.generate_project_context_modal")


class GenerateProjectContextModalPage(GenerateEntityModalPageBase):
    """Page object for the "Build with AI" Project Context generation modal."""

    #: The sole endpoint the modal calls to generate a draft
    #: (``GenerateProjectContextModal.jsx`` → ``generateProjectContextDraftApi.js``).
    GENERATE_DRAFT_ROUTE = "**/elitea_core/generate_project_context_draft/**"

    open_button = LocatorDescriptor(
        testid="generate-project-context-open-button",
        description='Editor toolbar\'s "Build with AI" button — rendered only while '
        "the editor content is empty (swapped for Edit with AI otherwise)",
    )

    title = LocatorDescriptor(
        testid="generate-project-context-title",
        description='Dialog title ("Build with AI") — identifies WHICH AI dialog is '
        "open, since the editor toolbar hosts two different ones",
    )

    modal = LocatorDescriptor(
        testid="generate-project-context-modal",
        description='"Build with AI" modal container (MUI Dialog root; no keepMounted, '
        "so its count is 0 while closed)",
    )

    prompt_input = LocatorDescriptor(
        testid="generate-project-context-prompt-input",
        description="Project-description textarea (input step)",
    )

    loading_indicator = LocatorDescriptor(
        testid="generate-project-context-loading-indicator",
        description='"Generating project context draft..." loading state',
    )

    generate_button = LocatorDescriptor(
        testid="generate-project-context-submit-button",
        description='"Generate Draft" button — also the retry control; disabled while '
        "the description is blank",
    )

    cancel_button = LocatorDescriptor(
        testid="generate-project-context-cancel-button",
        description="Cancel button (input step) — closes the dialog without generating",
    )

    approve_button = LocatorDescriptor(
        testid="generate-project-context-approve-button",
        description='"Apply" button (review step) — inserts the draft into the editor',
    )

    review_background_input = LocatorDescriptor(
        testid="generate-project-context-review-background-input",
        description="Review-form 'Project Background' textarea, pre-populated with the "
        "generated draft and editable before Apply",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def _is_generate_draft_url(self, url: str) -> bool:
        return "generate_project_context_draft" in url

    # ------------------------------------------------------------------
    # Review step
    # ------------------------------------------------------------------

    def get_review_background(self) -> str:
        """Return the review-form Project Background field's current value."""
        return self.review_background_input.input_value()

    def wait_for_review_form(self, timeout: int = 15000):
        """Wait for the review step, keyed on THIS entity's review handles.

        Overrides the base implementation, which waits on ``back_button`` +
        ``approve_button``. "Back to prompt" carries no testid for Project
        Context and deliberately does not get one: no case exercises it, and an
        unreferenced testid inflates the presence-based coverage metric
        (``.agents/testing.md`` § Locator policy, canon ruling #511). The review
        step is fully identified without it — ``Apply`` plus the populated
        Project Background field appear together and only on this step.
        """
        self.approve_button.wait_for(state="visible", timeout=timeout)
        self.review_background_input.wait_for(state="visible", timeout=timeout)

    @action("Click Apply")
    def click_apply(self) -> None:
        """Click "Apply" and wait for the dialog to close.

        ``GenerateEntityModal.handleApprove`` awaits ``onApprove`` and then
        ``handleClose``; for Project Context ``onApply`` only pushes the draft
        into the editor's local state — **no network call, and nothing is
        saved** (the ``PUT`` happens later, on Save). So the dialog's
        disappearance is the correct readiness condition, not a response wait.
        """
        self.approve_button.click()
        self.modal.wait_for(state="detached", timeout=15000)
        logger.info("Applied the generated Project Context draft")

    # ------------------------------------------------------------------
    # Cancel (input step)
    # ------------------------------------------------------------------

    @action("Cancel Build with AI")
    def click_cancel(self) -> None:
        """Click Cancel on the input step and wait for the dialog to close.

        Cancelling from the input step issues **no network request at all**
        (``handleClose`` merely resets local state), so the dialog's removal
        from the DOM is the only thing to wait on.
        """
        self.cancel_button.click()
        self.modal.wait_for(state="detached", timeout=10000)
        logger.info("Cancelled the Build with AI dialog")
