"""Toolkit detail page object.

URL: /app/toolkits/all/{id}

Provides methods for interacting with toolkit configuration and
verifying authentication status warnings.
"""

import logging

from playwright.sync_api import Page

from .base_page import BasePage

logger = logging.getLogger("elitea.pages.toolkit_detail")

UI_ELEMENT_TIMEOUT = 10_000


class ToolkitDetailPage(BasePage):
    """Toolkit detail/edit page.

    Provides methods for viewing and editing toolkit configuration,
    including checking for authentication warnings when credentials
    are invalid or expired.

    URL: /app/toolkits/all/{id}
    """

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_toolkit(self, toolkit_id: int) -> None:
        """Navigate to toolkit detail page and wait for load.

        Args:
            toolkit_id: Numeric toolkit ID.
        """
        self.navigate(f"/app/toolkits/all/{toolkit_id}")
        self.wait_for_page_load()

    def wait_for_page_load(self, timeout: int = 15000) -> None:
        """Wait for toolkit detail page to fully load.

        Waits for the form to render with the Toolkit Name field.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        name_field = self.page.get_by_role("textbox", name="Toolkit Name")
        name_field.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(1000)

    def get_authentication_warning(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get authentication warning message if present.

        Looks for warning messages starting with "Authentication failed:"
        that appear when toolkit credentials are invalid or expired.

        Different toolkit types and failed reasons show different messages:
        - Jira: "Authentication failed: Invalid bearer token"
        - GitHub: "Authentication failed: Invalid credentials"

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (warning message), or None if not found.
        """
        warning_locator = self.page.locator('div[aria-label^="Authentication failed:"]')
        try:
            warning_locator.nth(1).wait_for(state="visible", timeout=timeout)
            return warning_locator.nth(1).get_attribute("aria-label")
        except Exception:
            return None

    def has_authentication_warning(self, timeout: int = 5000) -> bool:
        """Check if authentication warning is displayed.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning is visible, False otherwise.
        """
        return self.get_authentication_warning(timeout=timeout) is not None

    def is_save_button_enabled(self) -> bool:
        """Check if Save button is enabled.

        Returns:
            True if Save button exists and is enabled, False otherwise.
        """
        save_btn = self.page.get_by_role("button", name="Save")
        if save_btn.count() == 0:
            return False
        return save_btn.first.is_enabled()

    def is_save_button_disabled(self) -> bool:
        """Check if Save button is disabled.

        Returns:
            True if Save button exists and is disabled, False otherwise.
        """
        save_btn = self.page.get_by_role("button", name="Save")
        if save_btn.count() == 0:
            return True
        return not save_btn.first.is_enabled()

    def get_toolkit_name(self) -> str:
        """Get the current toolkit name from the form.

        Returns:
            Toolkit name value.
        """
        name_field = self.page.get_by_role("textbox", name="Toolkit Name")
        return name_field.input_value()

    def get_description(self) -> str:
        """Get the current description from the form.

        Returns:
            Description value.
        """
        desc_field = self.page.get_by_role("textbox", name="Description")
        return desc_field.input_value()

    def fill_description(self, description: str) -> None:
        """Fill the description field.

        Args:
            description: New description text.
        """
        desc_field = self.page.get_by_role("textbox", name="Description")
        desc_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        desc_field.click()
        desc_field.select_text()
        desc_field.type(description)
        self.page.wait_for_timeout(500)

    def fill_toolkit_name(self, name: str) -> None:
        """Fill the toolkit name field.

        Args:
            name: New toolkit name.
        """
        name_field = self.page.get_by_role("textbox", name="Toolkit Name")
        name_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        name_field.click()
        name_field.select_text()
        name_field.type(name)
        self.page.wait_for_timeout(500)

    def click_save(self) -> None:
        """Click Save button and wait for network to settle.

        Raises:
            AssertionError: If Save button is not enabled.
        """
        save_btn = self.page.get_by_role("button", name="Save")
        save_btn.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        assert save_btn.first.is_enabled(), "Save button should be enabled before clicking"
        save_btn.first.click()
        self.wait_for_network()

    def click_discard(self) -> None:
        """Click Discard button to reset form changes."""
        discard_btn = self.page.get_by_role("button", name="Discard")
        discard_btn.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        discard_btn.first.click()
        self.page.wait_for_timeout(500)

    def get_configuration_dropdown_value(self) -> str | None:
        """Get the currently selected configuration (credential) name.

        Returns:
            Selected credential name or None if not found.
        """
        config_dropdown = self.page.locator('[class*="configuration"] [role="combobox"]')
        if config_dropdown.count() > 0:
            return config_dropdown.first.text_content()
        return None
