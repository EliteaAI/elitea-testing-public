"""Toolkit detail page object.

URL: /toolkits/all/{id}

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

from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.toolkit_detail")

UI_ELEMENT_TIMEOUT = 10_000


class ToolkitDetailPage(BasePage):
    """Toolkit detail/edit page.

    Provides methods for viewing and editing toolkit configuration,
    including checking for authentication warnings when credentials
    are invalid or expired.

    URL: /toolkits/all/{id}
    """

    # Page header showing the toolkit's own name (EditToolkit.jsx) — this
    # page's own identity element, added ELITEA-1866. NOT test-panel
    # specific (that's :class:`ToolkitTestSettingsPage`), which is why it
    # lives here rather than there (AFS § Overlap check).
    toolkit_title = LocatorDescriptor(
        testid="toolkit-detail-title",
        description="Toolkit-name header on the detail/config page "
        "(EditToolkit.jsx) — existing testid, already on "
        "automation/testids before this case",
    )

    # Configuration/Indexes tabs on the detail view's top tab strip
    # (EditToolkit.jsx). Both are icon-only with no visible text, so a
    # role-based `[role="tab"]` locator can't disambiguate them from each
    # other or from the page's own top-level tab — testids added ELITEA-1866
    # PR #670 review round 1 (`EliteaAI/EliteaUI` `automation/testids`
    # commit 0b61e8a2, via the `tabProps` mechanism already used for the
    # Indexes tab's `data-tour` attribute).
    configuration_tab = LocatorDescriptor(
        testid="toolkit-detail-configuration-tab",
        description="Configuration tab (icon-only, default-selected) on "
        "the detail view's top tab strip",
    )

    indexes_tab = LocatorDescriptor(
        testid="toolkit-detail-indexes-tab",
        description="Indexes tab (icon-only; disabled until Pgvector/"
        "Embedding Model are configured) on the detail view's top tab "
        "strip",
    )

    def __init__(self, page: Page):
        super().__init__(page)

    def get_toolkit_title(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the toolkit-detail page header's toolkit-name text.

        Args:
            timeout: Maximum wait time in milliseconds for the header to
                become visible.
        """
        self.toolkit_title.wait_for(state="visible", timeout=timeout)
        return self.toolkit_title.text_content() or ""

    def count_config_tabs(self, timeout: int = 5000) -> int:
        """Return how many of the Configuration/Indexes tabs are present.

        A compliant testid presence/count check against
        :attr:`configuration_tab`/:attr:`indexes_tab` — NOT a role-based
        ``[role="tab"]`` count (the page also renders other ``role="tab"``
        elements — see AFS § step 24 note re: an unexplained third tab
        element — so counting by role alone risks over-counting).

        Args:
            timeout: Maximum wait time in milliseconds for the
                Configuration tab (rendered first, default-selected) to
                appear before concluding neither tab is present.
        """
        try:
            self.configuration_tab.wait_for(state="visible", timeout=timeout)
        except Exception:
            return 0
        return self.configuration_tab.count() + self.indexes_tab.count()

    def navigate_to_toolkit(self, toolkit_id: int) -> None:
        """Navigate to toolkit detail page and wait for load.

        Args:
            toolkit_id: Numeric toolkit ID.
        """
        self.navigate(f"/toolkits/all/{toolkit_id}")
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
        """Get locator for credential warning message banner.

        Matches the BannerMessage component (data-testid="credential-warning-banner")
        that is rendered below the credential select field when credentials are invalid.
        Falls back to the old aria-label prefix selectors for backward compatibility.

        Returns:
            Locator matching the credential warning banner element.
        """
        return self.page.locator('[data-testid="credential-warning-banner"]')

    def get_authentication_warning(self, timeout: int = UI_ELEMENT_TIMEOUT) -> str | None:
        """Get authentication warning message if present.

        Looks for the BannerMessage error banner (data-testid="credential-warning-banner")
        that appears below the credential select field when credentials are invalid or
        expired.  The banner container has aria-label set to the error message text.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            The aria-label value (warning message), or None if not found.
        """
        warning_locator = self._get_warning_message_locator()
        try:
            warning_locator.first.wait_for(state="visible", timeout=timeout)
            return warning_locator.first.get_attribute("aria-label")
        except Exception:
            return None

    def has_authentication_warning(self, timeout: int = 5000) -> bool:
        """Check if authentication warning message is displayed.

        Args:
            timeout: Maximum wait time in milliseconds.

        Returns:
            True if warning banner is visible, False otherwise.
        """
        warning_locator = self._get_warning_message_locator()
        try:
            warning_locator.first.wait_for(state="visible", timeout=timeout)
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
        """Get locator for credential error indicator (the attention icon).

        Matches the attentionIconBox rendered inside CredentialOptionLabel when
        the selected credential is invalid (data-testid="credential-status-indicator").

        Falls back to aria-label prefix selectors for backward compatibility.

        Returns:
            Locator matching the credential status indicator icon.
        """
        return self.page.locator('[data-testid="credential-status-indicator"]')

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
        reload_btn = self.page.get_by_test_id("credential-reload-button")
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
        open_btn = self.page.get_by_test_id("credential-open-in-new-tab-button")
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
        reload_btn = self.page.get_by_test_id("credential-reload-button")
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
        reload_btn = self.page.get_by_test_id("credential-reload-button")
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
        open_btn = self.page.get_by_test_id("credential-open-in-new-tab-button")
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
        open_btn = self.page.get_by_test_id("credential-open-in-new-tab-button")
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

    # ------------------------------------------------------------------
    # Configuration credential-select (ToolBaseProperty.jsx -> CredentialsSelect.jsx)
    #
    # ELITEA-1976 — testid wiring: ToolBaseProperty.jsx's `type === 'configuration'`
    # branch passes `testId={`toolkit-field-${k}-select`}` to <CredentialsSelect>,
    # which threads it to the combobox (+ "-combobox" display suffix, same shared
    # mechanism `toolkit-test-tool-select`/`-combobox` already uses), the CREATE
    # section's two options (`-create-private`/`-create-project`), and the Saved-
    # credentials Refresh button (`-refresh-button`). Generic across every
    # credential-bearing toolkit type keyed off the schema field name `k` (e.g.
    # "gitlab_configuration", "github_configuration", "jira_configuration") — a
    # dynamic class-constant template per .agents/testing.md § Locator policy.
    # This case only exercises "gitlab_configuration"; other field keys are for
    # whichever future case exercises them (role-overrides.md § "touches" rule).
    # ------------------------------------------------------------------
    CONFIGURATION_SELECT = '[data-testid="toolkit-field-{}-select"]'
    CONFIGURATION_SELECT_COMBOBOX = '[data-testid="toolkit-field-{}-select-combobox"]'
    # Both the "CREATE" and "Saved ... Credentials" group headers share this
    # SAME testid (SingleSelect.jsx's ListSubheader — generic across every
    # grouped-option Select). Disambiguate by position: CREATE always renders
    # first (Object.entries(menuData) insertion order — CredentialsSelect.jsx's
    # menuData `useMemo` always pushes "Create" before "Saved ... Credentials").
    CONFIGURATION_SELECT_GROUP_HEADER = '[data-testid="toolkit-field-{}-select-group-header"]'
    CONFIGURATION_SELECT_CREATE_PRIVATE = '[data-testid="toolkit-field-{}-select-create-private"]'
    CONFIGURATION_SELECT_CREATE_PROJECT = '[data-testid="toolkit-field-{}-select-create-project"]'
    CONFIGURATION_SELECT_REFRESH_BUTTON = '[data-testid="toolkit-field-{}-select-refresh-button"]'
    # Saved-credential option row — SingleSelectMenuItem.jsx's PRE-EXISTING
    # `data-testid={option.testId ?? `select-option-${option.value}`}` fallback
    # already produces this (zero JSX change needed); value shape mirrors
    # CredentialsSelect.jsx's savedRowToSelectValue():
    # JSON.stringify({kind: "saved", elitea_title, private}).
    CONFIGURATION_SAVED_CREDENTIAL_OPTION = (
        '[data-testid=\'select-option-{{"kind":"saved","elitea_title":"{}","private":{}}}\']'
    )

    def configuration_select(self, field_key: str) -> Locator:
        """Return the Configuration credential-select combobox for *field_key*.

        Args:
            field_key: The toolkit's configuration schema field name (e.g.
                ``"gitlab_configuration"``).
        """
        return self.page.locator(self.CONFIGURATION_SELECT.format(field_key))

    def open_configuration_dropdown(self, field_key: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the Configuration select for *field_key* to open its dropdown."""
        select = self.configuration_select(field_key)
        select.wait_for(state="visible", timeout=timeout)
        select.click()
        logger.info("Opened Configuration dropdown for field_key=%s", field_key)

    def configuration_group_headers(self, field_key: str) -> Locator:
        """Return both group headers ("CREATE" + "Saved ... Credentials") for *field_key*.

        Both share one testid; index by position — CREATE is index 0 (see
        class-level comment on :data:`CONFIGURATION_SELECT_GROUP_HEADER`).
        """
        return self.page.locator(self.CONFIGURATION_SELECT_GROUP_HEADER.format(field_key))

    def get_configuration_display_text(self, field_key: str, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
        """Return the Configuration select's currently displayed value text.

        Reads the "-combobox" suffixed display element (``SelectDisplayProps``
        target — the same shared mechanism ``toolkit-test-tool-select``/
        ``-combobox`` already uses), not the outer select root.
        """
        combobox = self.page.locator(self.CONFIGURATION_SELECT_COMBOBOX.format(field_key))
        combobox.wait_for(state="visible", timeout=timeout)
        return combobox.text_content() or ""

    def configuration_create_private_option(self, field_key: str) -> Locator:
        """Return the CREATE section's 'New private ... credentials' option."""
        return self.page.locator(self.CONFIGURATION_SELECT_CREATE_PRIVATE.format(field_key))

    def configuration_create_project_option(self, field_key: str) -> Locator:
        """Return the CREATE section's 'New project ... credentials' option."""
        return self.page.locator(self.CONFIGURATION_SELECT_CREATE_PROJECT.format(field_key))

    def click_create_private_credential(self, field_key: str, timeout: int = UI_ELEMENT_TIMEOUT) -> Page:
        """Click 'New private ... credentials' and return the new tab.

        Opens in a real new browser tab (``window.open(..., '_blank', ...)``)
        — the credential-create form for this toolkit's configuration type,
        pre-selected, under the acting user's PERSONAL project context.

        Returns:
            The new tab's :class:`~playwright.sync_api.Page`, already waited
            for ``domcontentloaded``.
        """
        option = self.configuration_create_private_option(field_key)
        option.wait_for(state="visible", timeout=timeout)
        with self.page.context.expect_page() as new_page_info:
            option.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Clicked 'New private credentials' for field_key=%s — new tab: %s", field_key, new_page.url)
        return new_page

    def configuration_refresh_button(self, field_key: str) -> Locator:
        """Return the Refresh button next to the 'Saved ... Credentials' header."""
        return self.page.locator(self.CONFIGURATION_SELECT_REFRESH_BUTTON.format(field_key))

    def click_configuration_refresh(self, field_key: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the Configuration select's Refresh button and wait for the network."""
        button = self.configuration_refresh_button(field_key)
        button.wait_for(state="visible", timeout=timeout)
        button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked Configuration refresh for field_key=%s", field_key)

    def saved_credential_option(self, elitea_title: str, private: bool) -> Locator:
        """Return the Saved-credentials list row for *elitea_title*/*private*."""
        return self.page.locator(
            self.CONFIGURATION_SAVED_CREDENTIAL_OPTION.format(elitea_title, str(bool(private)).lower())
        )

    def select_saved_credential(
        self, elitea_title: str, private: bool, timeout: int = UI_ELEMENT_TIMEOUT
    ) -> None:
        """Click the Saved-credentials row matching *elitea_title*/*private*."""
        option = self.saved_credential_option(elitea_title, private)
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("Selected saved credential elitea_title=%s private=%s", elitea_title, private)
