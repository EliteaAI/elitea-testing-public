"""Pipeline form page object for create/edit operations.

Handles pipeline form filling, save/cancel/discard operations.

URL: /pipelines/create, /pipelines/all/{id}
"""

import logging
from playwright.sync_api import Page
from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from components.mui import Dialog

logger = logging.getLogger("elitea.pages.pipeline_form")


class PipelineFormPage(BasePage):
    """Pipeline create/edit form page.

    Handles:
    - Form field operations (name, description)
    - Save/cancel/discard actions
    - Form validation waits
    - MUI form patterns (click + type instead of fill)

    URL: /pipelines/create or /pipelines/all/{id}
    """

    # LocatorDescriptors - testid + fallback pattern
    name_input = LocatorDescriptor(
        testid="agent-name-input",
        fallback=lambda page: page.get_by_role("textbox", name="Name"),
        description="Pipeline name input field"
    )

    description_input = LocatorDescriptor(
        testid="agent-description-input",
        fallback=lambda page: page.get_by_role("textbox", name="Description"),
        description="Pipeline description input field"
    )

    save_button = LocatorDescriptor(
        testid="agent-save-button",
        fallback=lambda page: page.get_by_role("button", name="Save", exact=True),
        description="Save pipeline button"
    )

    cancel_button = LocatorDescriptor(
        fallback=lambda page: page.get_by_role("button", name="Cancel"),
        description="Cancel button"
    )

    discard_button = LocatorDescriptor(
        testid="discard-button",
        description="Discard changes button (ApplicationTabBar.jsx — the pipeline "
        "detail page reuses the application tab bar). Rendered unconditionally; "
        "only `disabled` toggles with form dirtiness, so it is always visible. "
        "The `fallback=` that used to sit here was dead code — LocatorDescriptor "
        "never invokes it when a testid is set — and it masked nothing: the "
        "testid was simply not reaching the DOM until the call site was fixed "
        "to pass DiscardButton's `dataTestId` prop instead of `data-testid`.",
    )

    # "Save As Version" button (SaveNewVersionButton.jsx, rendered via
    # ApplicationTabBar.jsx — the same shared component AgentFormPage.
    # save_as_version_button already wires; EditPipeline.jsx reuses
    # ApplicationTabBar.jsx too). Confirmed live end-to-end on a pipeline
    # detail page (ELITEA-2002 exploration, 2026-08-07): enabled only when
    # the form is dirty (mirrors save_button/discard_button's dirtiness
    # gating), zero add-data-testid work needed — the testid already
    # reaches the DOM via the shared component.
    save_as_version_button = LocatorDescriptor(
        testid="agent-save-as-version-button",
        description="Save current edits as a new pipeline version button",
    )

    # Tags combobox (ELITEA-2021). Testid-only, added via add-data-testid onto
    # the shared TagEditor/AutoCompleteDropDown component's `inputTestId`/
    # `chipTestId` hooks (ApplicationEditForm.jsx, pipeline branch only —
    # canon #511 scope discipline: no case exercises Agent's Tags yet).
    tags_input = LocatorDescriptor(
        testid="pipeline-tags-input",
        description="Tags Autocomplete input field (real <input>, MUI TextField)",
    )

    tags_chip = LocatorDescriptor(
        testid="pipeline-tags-chip",
        description="Rendered tag chip in the Tags field (one per committed tag)",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to_create(self):
        """Navigate to create pipeline page and wait for form load."""
        super().navigate("/pipelines/create?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to create pipeline page")

    def navigate_to_edit(self, pipeline_id: int):
        """Navigate to pipeline edit page and wait for form load.

        Args:
            pipeline_id: The numeric pipeline ID.
        """
        super().navigate(f"/pipelines/all/{pipeline_id}?viewMode=owner")
        self.wait_for_page_load()
        logger.info("Navigated to pipeline %d edit page", pipeline_id)

    # ------------------------------------------------------------------
    # Wait methods
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the pipeline form to fully load.

        Waits for name field to be visible and network to settle.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.name_input.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=10000)
        self.page.wait_for_timeout(1000)  # Form initialization
        logger.info("Pipeline form loaded")

    def wait_for_form_validation(self, timeout: int = 1000):
        """Wait for MUI form validation to complete.

        MUI forms have debounce delay for validation (300-500ms).
        Pages with persistent WebSocket connections never reach networkidle,
        so any TimeoutError is silently ignored here.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            pass  # Pages with WebSocket may never reach networkidle
        self.page.wait_for_timeout(500)  # MUI debounce

    # ------------------------------------------------------------------
    # Form operations
    # ------------------------------------------------------------------

    def fill_form(self, name: str, description: str):
        """Fill in the pipeline create/edit form.

        Uses click() + type() instead of fill() because MUI React forms
        do not recognize programmatic fill() value changes.

        Args:
            name: Pipeline name (required).
            description: Pipeline description (required).
        """
        logger.info("Filling pipeline form: name=%s", name)

        # Name field
        self.name_input.click()
        self.name_input.type(name)
        self.page.wait_for_timeout(200)

        # Description field
        self.description_input.click()
        self.description_input.type(description)
        self.page.wait_for_timeout(200)

    def update_text_field(self, field_name: str, value: str, wait_for_validation: bool = True):
        """Update a text field using React onChange pattern.

        Uses click + select all + type to trigger React onChange event.

        Args:
            field_name: Field to update ("name" or "description").
            value: New value for the field.
            wait_for_validation: Whether to wait for form validation after update.
        """
        field_map = {
            "name": self.name_input,
            "description": self.description_input,
        }

        if field_name not in field_map:
            raise ValueError(f"Unknown field: {field_name}. Must be 'name' or 'description'")

        field = field_map[field_name]
        field.click()
        # el.select() is the only reliable way to select all text in a React-controlled
        # MUI input/textarea: Ctrl+A via Playwright press() doesn't always propagate to
        # the native selection (React may consume the event without selecting).
        field.evaluate("el => el.select()")
        self.page.keyboard.type(value)

        if wait_for_validation:
            self.wait_for_form_validation()

    def update_name(self, name: str):
        """Update pipeline name field.

        Args:
            name: New name value.
        """
        self.update_text_field("name", name)

    def update_description(self, description: str):
        """Update pipeline description field.

        Args:
            description: New description value.
        """
        self.update_text_field("description", description)

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_name(self) -> str:
        """Read the current value of the Name field.

        Returns:
            Current name input value.
        """
        return self.name_input.input_value()

    def get_description(self) -> str:
        """Read the current value of the Description field.

        Returns:
            Current description input value.
        """
        return self.description_input.input_value()

    # ------------------------------------------------------------------
    # Tags (ELITEA-2021)
    # ------------------------------------------------------------------

    def add_tag(self, tag_name: str, timeout: int = 5000):
        """Type a tag into the Tags combobox and commit it with Enter.

        The field's placeholder literally reads "Type a tag and press
        comma/enter" (AutoCompleteDropDown's freeSolo Autocomplete) —
        Enter commits the typed text as a chip.

        Args:
            tag_name: Tag text to type and commit.
            timeout: Maximum wait time for the input to be visible.
        """
        logger.info("Adding tag '%s'", tag_name)
        self.tags_input.wait_for(state="visible", timeout=timeout)
        self.tags_input.click()
        self.tags_input.press_sequentially(tag_name, delay=20)
        self.tags_input.press("Enter")
        self.page.wait_for_timeout(300)

    def get_tag_chip_text(self, timeout: int = 5000) -> str:
        """Read the text of the first rendered tag chip.

        Args:
            timeout: Maximum wait time for the chip to be visible.

        Returns:
            The chip's visible text (trimmed).
        """
        chip = self.tags_chip.first
        chip.wait_for(state="visible", timeout=timeout)
        return (chip.text_content() or "").strip()

    # ------------------------------------------------------------------
    # Save/Cancel/Discard actions
    # ------------------------------------------------------------------

    def click_save(self, timeout: int = 10000):
        """Click the Save button and wait for network.

        Uses JavaScript click to bypass MUI overlay interception.

        Args:
            timeout: Maximum wait time for save to complete.
        """
        logger.info("Clicking Save")
        self.save_button.evaluate("el => el.click()")
        self.wait_for_network(timeout=timeout)

    def save_and_wait_for_navigation(self, timeout: int = 15000):
        """Click Save and wait for navigation to detail page.

        Encapsulates save + navigation + detail page load wait.

        Args:
            timeout: Maximum wait time for save and navigation.
        """
        self.click_save(timeout=timeout)
        # After save on create, URL changes to /pipelines/all/{id}
        # Wait for URL to change
        self.page.wait_for_url("**/pipelines/all/*", timeout=timeout)
        self.wait_for_network(timeout=10000)

    def save_and_wait_for_creation(self, project_id: str, timeout: int = 15000) -> dict:
        """Click Save on the create form and wait for the create POST's 2xx response.

        Waits on the network response itself (not just navigation), so a
        non-2xx create failure surfaces here rather than downstream. Mirrors
        ``PipelineDetailPage.save_and_wait_for_update`` (ELITEA-1954), the
        create-side equivalent — additive, no existing caller touched.

        Args:
            project_id: Project id, used to scope the response URL match.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Parsed JSON body of the create response.
        """
        with self.page.expect_response(
            lambda r: f"/applications/prompt_lib/{project_id}" in r.url
            and r.request.method == "POST"
            and 200 <= r.status < 300,
            timeout=timeout,
        ) as response_info:
            self.save_button.evaluate("el => el.click()")
        self.page.wait_for_url("**/pipelines/all/*", timeout=timeout)
        self.wait_for_network(timeout=10000)
        return response_info.value.json()

    def is_save_enabled(self) -> bool:
        """Check if the Save button is enabled.

        Returns:
            True if save button is enabled, False otherwise.
        """
        return self.save_button.is_enabled()

    def click_cancel(self):
        """Click the Cancel button."""
        logger.info("Clicking Cancel")
        self.cancel_button.click()
        self.page.wait_for_timeout(500)

    def click_discard(self, timeout: int = 5000):
        """Click the Discard button and confirm dialog if present.

        The Discard button reverts unsaved changes. It may show a
        confirmation dialog.

        Args:
            timeout: Maximum wait time for discard action.
        """
        logger.info("Clicking Discard")
        self.dismiss_banner_if_present()
        self.discard_button.wait_for(state="visible", timeout=timeout)
        self.discard_button.evaluate("el => el.click()")
        self.page.wait_for_timeout(500)

        # Handle confirmation dialog if present
        try:
            dialog = Dialog.wait_for(self.page, timeout=3000)
            Dialog.click_first_button(dialog, "Discard", "Confirm")
        except Exception:
            pass  # No confirmation dialog

        self.wait_for_network(timeout=timeout)
        logger.info("Discard clicked")

    def is_discard_enabled(self) -> bool:
        """Check if the Discard button is visible and enabled.

        Returns:
            True if discard button is enabled, False otherwise.
        """
        return (
            self.discard_button.is_visible()
            and self.discard_button.is_enabled()
        )

    def is_save_as_version_enabled(self) -> bool:
        """Check if the Save As Version button is enabled.

        Mirrors :meth:`is_save_enabled` — same dirtiness-gated shared
        button family (ApplicationTabBar.jsx).

        Returns:
            True if Save As Version is enabled, False otherwise.
        """
        return self.save_as_version_button.is_enabled()
