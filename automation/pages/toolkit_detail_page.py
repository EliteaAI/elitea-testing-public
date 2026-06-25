"""Toolkit detail page object.

URL: /app/toolkits/all/{id}

Provides methods for interacting with toolkit configuration and
verifying authentication status warnings, including status indicators
for invalid credentials (status indicator, warning message, reload, open in new tab).

Enhancement #5114: Added support for credential status indicators:
- Status indicator for invalid/expired credentials
- Warning message explaining the authentication failure
- Reload button to refresh credential status
- Open in new tab button to view credential details
"""

import logging
import re

from playwright.sync_api import Page, expect

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

    def _get_warning_message_locator(self):
        """Get locator for credential warning message.

        Matches various error messages:
        - "Authentication failed: ..."
        - "Access forbidden: ..."
        - "Connection error: ..."

        Returns:
            Locator matching any credential warning message.
        """
        return self.page.locator(
            'div[aria-label^="Authentication failed:"], '
            'div[aria-label^="Access forbidden:"], '
            'div[aria-label^="Connection error:"]'
        )

    def get_authentication_warning(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get authentication warning message if present.

        Looks for warning messages that appear when toolkit credentials
        are invalid or expired.

        Different error types:
        - "Authentication failed: Invalid bearer token"
        - "Access forbidden: Your account has insufficient..."
        - "Connection error: ..."

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (warning message), or None if not found.
        """
        warning_locator = self._get_warning_message_locator()
        try:
            warning_locator.nth(1).wait_for(state="visible", timeout=timeout)
            return warning_locator.nth(1).get_attribute("aria-label")
        except Exception:
            return None

    def has_authentication_warning(self, timeout: int = 5000) -> bool:
        """Check if authentication warning message is displayed.

        Note: The warning icon is the first element (.first),
        the warning message text is the second element (.nth(1)).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning message is visible, False otherwise.
        """
        warning_locator = self._get_warning_message_locator()
        try:
            if warning_locator.count() < 2:
                return False
            warning_locator.nth(1).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

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

    # ------------------------------------------------------------------
    # Credential status indicators (Enhancement #5114)
    # ------------------------------------------------------------------

    def _get_credential_row(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Get the credential row element containing dropdown and action buttons.

        Locator: [data-tour="shared-tool-configuration-form"] [aria-labelledby*="Configuration"]

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator for the credential row element.
        """
        row = self.page.locator(
            '[data-tour="shared-tool-configuration-form"] [aria-labelledby*="Configuration"]'
        )
        row.first.wait_for(state="visible", timeout=timeout)
        return row.first

    def hover_credential_row(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Hover over the credential row to reveal status indicator icons.

        The reload and open-in-new-tab icons are only visible on hover.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        row = self._get_credential_row(timeout)
        row.hover()
        self.page.wait_for_timeout(500)

    def _get_credential_error_locator(self):
        """Get locator for credential error indicator.

        Matches various error messages:
        - "Authentication failed: ..."
        - "Access forbidden: ..."
        - "Connection error: ..."

        Returns:
            Locator matching any credential error indicator.
        """
        return self.page.locator(
            'div[aria-label^="Authentication failed:"], '
            'div[aria-label^="Access forbidden:"], '
            'div[aria-label^="Connection error:"]'
        )

    def has_credential_status_indicator(self, timeout: int = 5000) -> bool:
        """Check if credential status indicator (warning icon) is displayed.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if status indicator is visible, False otherwise.
        """
        warning_locator = self._get_credential_error_locator()
        try:
            warning_locator.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_credential_status_indicator_tooltip(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get the status indicator tooltip text (aria-label).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        warning_locator = self._get_credential_error_locator()
        try:
            warning_locator.first.wait_for(state="visible", timeout=timeout)
            return warning_locator.first.get_attribute("aria-label")
        except Exception:
            return None

    def click_credential_reload(self, timeout: int = UI_ELEMENT_TIMEOUT):
        """Click the reload button to refresh credential status.

        Hovers over the credential row first to reveal the button,
        then clicks it and waits for the status to update.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.hover_credential_row(timeout)
        reload_btn = self.page.locator('button[aria-label="Reload and apply changes"]')
        reload_btn.wait_for(state="visible", timeout=timeout)
        reload_btn.click()
        self.wait_for_network(timeout=timeout)
        self.page.wait_for_timeout(3000)
        logger.info("Clicked credential reload button")

    def click_credential_open_in_new_tab(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Click the open-in-new-tab button for the credential.

        Hovers over the credential row first to reveal the button,
        then clicks it. The credential detail page opens in a new tab.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            URL of the new tab (credential detail page).
        """
        self.hover_credential_row(timeout)
        open_btn = self.page.locator('button[aria-label="Open in new tab"]')
        open_btn.wait_for(state="visible", timeout=timeout)

        with self.page.context.expect_page() as new_page_info:
            open_btn.click()

        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        url = new_page.url
        new_page.close()
        logger.info("Opened credential in new tab: %s", url)
        return url

    def has_reload_button(self, timeout: int = 5000) -> bool:
        """Check if reload button is visible (after hovering).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if reload button exists and is visible.
        """
        self.hover_credential_row(timeout)
        reload_btn = self.page.locator('button[aria-label="Reload and apply changes"]')
        try:
            reload_btn.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_reload_button_tooltip(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get the reload button tooltip text (aria-label).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_credential_row(timeout)
        reload_btn = self.page.locator('button[aria-label="Reload and apply changes"]')
        try:
            reload_btn.wait_for(state="visible", timeout=timeout)
            return reload_btn.get_attribute("aria-label")
        except Exception:
            return None

    def has_open_in_new_tab_button(self, timeout: int = 5000) -> bool:
        """Check if open-in-new-tab button is visible (after hovering).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if open-in-new-tab button exists and is visible.
        """
        self.hover_credential_row(timeout)
        open_btn = self.page.locator('button[aria-label="Open in new tab"]')
        try:
            open_btn.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def get_open_in_new_tab_button_tooltip(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get the open-in-new-tab button tooltip text (aria-label).

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (tooltip text), or None if not found.
        """
        self.hover_credential_row(timeout)
        open_btn = self.page.locator('button[aria-label="Open in new tab"]')
        try:
            open_btn.wait_for(state="visible", timeout=timeout)
            return open_btn.get_attribute("aria-label")
        except Exception:
            return None

    def wait_for_no_status_indicator(self, timeout: int = 15000):
        """Wait for the credential status indicator to disappear.

        Used after fixing invalid credentials to verify the warning
        is no longer displayed.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        warning_locator = self._get_credential_error_locator()
        expect(warning_locator.first).not_to_be_visible(timeout=timeout)
        logger.info("Status indicator is no longer visible")
