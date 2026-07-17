"""Shared base for "Build with AI" entity-draft generation modal page objects.

Both the Agent and Skill "Build with AI" flows render the same shared
``GenerateEntityModal.jsx`` / ``GenerateEntityButton.jsx`` presentation
components (via ``entityLabel="agent"`` / ``entityLabel="skill"``), so the
modal shell behavior (loading -> error -> retry -> review) is identical
across entities. Only the concrete testids (per-entity naming convention,
``generate-agent-*`` vs ``generate-skill-*``) and the generate-draft
network route differ.

Subclasses supply:
- ``GENERATE_DRAFT_ROUTE`` — the entity-specific generate-draft endpoint glob.
- All ``LocatorDescriptor`` fields declared as ``None`` placeholders here
  (open_button, modal, close_button, prompt_input, error_alert,
  loading_indicator, generate_button, cancel_button, back_button,
  approve_button) — each entity wrapper wires its own testid naming
  convention (e.g. ``generate-agent-open-button`` vs
  ``generate-skill-open-button``).

Do NOT instantiate this base directly — it has no route or locators of its
own. See ``generate_agent_modal_page.py`` / ``generate_skill_modal_page.py``
for the concrete entity page objects.
"""

import json
import logging

from playwright.sync_api import Page

from .base_page import BasePage
from utils.actions import action


logger = logging.getLogger("elitea.pages.generate_entity_modal")


class GenerateEntityModalPageBase(BasePage):
    """Base page object for the shared "Build with AI" generation modal.

    Subclasses must set ``GENERATE_DRAFT_ROUTE`` and override every
    locator field below with a concrete ``LocatorDescriptor``.
    """

    # Override in subclass: the entity-specific generate-draft endpoint glob.
    GENERATE_DRAFT_ROUTE: str = None

    # Locator placeholders — overridden by subclasses with real
    # LocatorDescriptor(testid=...) fields per entity naming convention.
    open_button = None
    modal = None
    close_button = None
    prompt_input = None
    error_alert = None
    loading_indicator = None
    generate_button = None
    cancel_button = None
    back_button = None
    approve_button = None

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    @action("Open Build with AI modal")
    def open_modal(self, timeout: int = 5000):
        """Click the "Build with AI" button and wait for the modal to open."""
        self.open_button.click()
        self.modal.wait_for(state="visible", timeout=timeout)
        logger.info("Build with AI modal opened")

    # ------------------------------------------------------------------
    # Prompt input
    # ------------------------------------------------------------------

    @action("Fill prompt")
    def fill_prompt(self, text: str):
        """Fill the prompt textarea. testid resolves to the native <textarea>
        (wired via ``inputProps``), so a plain ``fill()`` triggers React's
        onChange correctly.
        """
        self.prompt_input.click()
        self.prompt_input.fill(text)
        logger.info("Filled prompt: %d characters", len(text))

    def get_prompt_value(self) -> str:
        """Read the current value of the prompt textarea."""
        return self.prompt_input.input_value()

    def is_generate_enabled(self) -> bool:
        """Check if the Generate button is enabled."""
        return self.generate_button.is_enabled()

    # ------------------------------------------------------------------
    # Network mocking — generate-draft endpoint
    # ------------------------------------------------------------------

    def mock_generate_failure(
        self,
        error_message: str,
        status: int = 500,
        delay_ms: int = 300,
    ):
        """Install a route mock that fails the generate-draft call.

        Args:
            error_message: Body ``error`` field — surfaced verbatim by
                ``GenerateEntityModal.jsx``'s ``generateError?.data?.error``.
            status: HTTP status to fulfill with.
            delay_ms: Artificial latency before fulfilling, so the transient
                loading state is reliably observable by the test (a 0-delay
                mock can resolve before the next assertion runs).
        """
        def handler(route):
            self.page.wait_for_timeout(delay_ms)
            route.fulfill(
                status=status,
                content_type="application/json",
                body=json.dumps({"error": error_message}),
            )

        self.page.route(self.GENERATE_DRAFT_ROUTE, handler)
        logger.info("Mocked generate-draft failure: status=%d error=%r", status, error_message)

    def mock_generate_success(self, draft: dict, delay_ms: int = 300):
        """Install a route mock that returns a synthetic successful draft.

        Args:
            draft: Draft payload consumed directly by the entity's review
                form (field set is entity-specific — see subclass docstring).
            delay_ms: Artificial latency before fulfilling, so the transient
                loading state is reliably observable by the test.
        """
        def handler(route):
            self.page.wait_for_timeout(delay_ms)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(draft),
            )

        self.page.route(self.GENERATE_DRAFT_ROUTE, handler)
        logger.info("Mocked generate-draft success: draft name=%r", draft.get("name"))

    def clear_generate_mock(self):
        """Remove any route mock on the generate-draft endpoint."""
        self.page.unroute(self.GENERATE_DRAFT_ROUTE)
        logger.info("Cleared generate-draft route mock")

    # ------------------------------------------------------------------
    # Generate / retry
    # ------------------------------------------------------------------

    def expect_generate_response(self, timeout: int = 15000):
        """Context manager: yields Playwright's response-info handle for the
        generate-draft call, resolved once the block exits.

        Usage::

            with modal.expect_generate_response() as response_info:
                modal.generate_button.click()
                # any interim assertions the caller wants to make while the
                # (possibly artificially delayed) mocked request is in flight
            response = response_info.value
        """
        return self.page.expect_response(
            lambda response: self._is_generate_draft_url(response.url),
            timeout=timeout,
        )

    def _is_generate_draft_url(self, url: str) -> bool:
        """Match a response URL against this entity's generate-draft route.

        Subclasses may override for a more precise match than the glob
        substring check performed here.
        """
        raise NotImplementedError(
            "Subclasses must implement _is_generate_draft_url()"
        )

    @action("Click Generate")
    def click_generate_and_wait_for_response(self, timeout: int = 15000):
        """Click Generate (also used as the retry control) and return the
        network response for the generate-draft call.

        Uses ``page.expect_response`` so the wait is tied to the real
        network event, not a fixed sleep.
        """
        with self.expect_generate_response(timeout=timeout) as response_info:
            self.generate_button.click()
        response = response_info.value
        logger.info("Generate-draft response: %d %s", response.status, response.url)
        return response

    # ------------------------------------------------------------------
    # State getters
    # ------------------------------------------------------------------

    def is_error_alert_visible(self, timeout: int = 5000) -> bool:
        """Check whether the error alert is currently visible."""
        try:
            return self.error_alert.is_visible(timeout=timeout)
        except Exception:
            return False

    def get_error_message(self) -> str:
        """Read the error alert's text content."""
        return self.error_alert.text_content() or ""

    def wait_for_loading_visible(self, timeout: int = 3000):
        """Wait for the "Generating <entity> draft..." loading state to appear."""
        self.loading_indicator.wait_for(state="visible", timeout=timeout)

    def wait_for_loading_hidden(self, timeout: int = 15000):
        """Wait for the loading state to disappear (request settled)."""
        self.loading_indicator.wait_for(state="hidden", timeout=timeout)

    def wait_for_review_form(self, timeout: int = 15000):
        """Wait for the review-form step's action buttons to appear,
        confirming the modal transitioned from loading to review."""
        self.back_button.wait_for(state="visible", timeout=timeout)
        self.approve_button.wait_for(state="visible", timeout=timeout)

    def wait_for_input_step(self, timeout: int = 5000):
        """Wait for the input step (Generate button) to (re)appear —
        e.g. after a failed generation reverts the modal from loading."""
        self.generate_button.wait_for(state="visible", timeout=timeout)

    def wait_for_input_step_hidden(self, timeout: int = 5000):
        """Wait for the input step (Generate button) to disappear — e.g.
        once a successful retry has moved the modal to the review step."""
        self.generate_button.wait_for(state="hidden", timeout=timeout)
