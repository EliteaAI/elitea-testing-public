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

import json
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

    # Indexes has now moved TWICE, and this field tracks the second move.
    #   1. EliteaUI EL-5947 removed the standalone Indexes *tab*
    #      (`toolkit-detail-indexes-tab`) and folded Indexes INTO the
    #      Configuration tab as an accordion (`toolkit-indexes-accordion`).
    #   2. A further redesign (elitea-testing-public#1616, live-confirmed
    #      2026-08-27) removed the accordion too: Indexes is now a
    #      right-hand SIDE PANEL inside the Configuration tab —
    #      `IndexesPanel.jsx`, root `toolkit-indexes-panel`, rendered by
    #      `ConfigurationTab.jsx` whenever the toolkit's schema exposes
    #      index tools. `toolkit-indexes-accordion` is absent from BOTH
    #      `origin/main` and `origin/automation/testids`.
    #
    # Use the panel's ROOT, never its contents: on a bare toolkit with no
    # PgVector connection / Embedding Model configured, `indexingBlocker`
    # is set and the panel renders only its banner — `toolkit-indexes-count`,
    # `toolkit-indexes-add-button` and `toolkit-indexes-empty-state` are all
    # absent at runtime despite existing on `main`. The panel root is the
    # only handle that honestly proves the Indexes surface is reachable in
    # that state.
    indexes_panel = LocatorDescriptor(
        testid="toolkit-indexes-panel",
        description="Indexes side panel (IndexesPanel.jsx root) rendered "
        "beside the Configuration form on the toolkit detail view — "
        "replaced the former Indexes accordion (#1616), which itself had "
        "replaced the standalone Indexes tab (EL-5947)",
    )

    # Action-bar "Test" button on the detail view (ToolkitForm.jsx, rendered
    # when `isDetailsActionBar && handleShowTest`). This is the PRODUCT's own
    # route to the Test surface, which the #1616 redesign moved out of the
    # detail view entirely and onto `/toolkits/:tab/:toolkitId/test`. The
    # button is disabled while the form is dirty; it is enabled immediately
    # after a Save.
    test_button = LocatorDescriptor(
        testid="toolkit-test-button",
        description="'Test' button in the toolkit detail view's action bar "
        "— navigates to the standalone Test Toolkit surface at "
        "/toolkits/{tab}/{id}/test",
    )

    # ------------------------------------------------------------------
    # Credential Configuration dropdown (CredentialsSelect.jsx) — added
    # for ELITEA-1976/1979. Testid added via add-data-testid:
    # `dataTestId={`toolkit-credential-select-${type}`}` on the underlying
    # Select.SingleSelect, which auto-suffixes "-combobox" onto the
    # interactive role=combobox node (SelectDisplayProps) — same mechanism
    # already used by ChatPage.project_selector_trigger
    # ("project-selector-trigger-combobox").
    # ------------------------------------------------------------------
    CREDENTIAL_SELECT_TRIGGER = '[data-testid="toolkit-credential-select-{}-combobox"]'

    # Dropdown-option testid family (shared SingleSelectMenuItem.jsx /
    # SingleSelect.jsx action-branch, same template shape as
    # ToolkitTestSettingsPage.TOOL_OPTION). Value is the app's own
    # JSON.stringify()'d select value — built by :meth:`_create_option_value`
    # / :meth:`_saved_option_value` to match it exactly.
    # Single-quoted attribute value — the encoded value itself contains
    # double quotes (JSON), which would otherwise break the CSS selector.
    SELECT_OPTION = "[data-testid='select-option-{}']"

    # Group-header text ("CREATE" / "Saved {type} Credentials", rendered
    # visually uppercase via CSS text-transform) — testid added for
    # ELITEA-1976 (SingleSelect.jsx renderMenuItems, keyed by group.key,
    # which CredentialsSelect.jsx sets to the raw group title).
    SELECT_GROUP_HEADER = '[data-testid="select-group-header-{}"]'

    credential_select_refresh_button = LocatorDescriptor(
        testid="credential-select-refresh-button",
        description="'Refresh the configurations' button inside the Saved "
        "Credentials subheader (CredentialsSelect.jsx) — testid added for "
        "ELITEA-1976",
    )

    credential_select_mismatch_footer = LocatorDescriptor(
        testid="credential-select-mismatch-footer",
        description="'Your configuration does not match any available "
        "configurations.' helper text shown when the linked credential's "
        "elitea_title no longer resolves against any fetched configuration "
        "(CredentialMismatchFooter.jsx) — testid added for ELITEA-1979",
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

    def wait_for_config_surface(self, timeout: int = 5000) -> None:
        """Wait until the detail view's configuration surface has rendered.

        Replaces the former ``count_config_tabs()``, whose contract ("count
        the Configuration *and Indexes* tabs, expect >= 2") described a
        two-tab strip that no longer exists (EliteaUI EL-5947).

        Waits on the **Indexes side panel**, not the Configuration tab: the
        detail view's tab array now holds exactly ONE entry, so the strip
        itself is not displayed and ``configuration_tab`` resolves to a
        HIDDEN ``role="tab"`` element — present and ``aria-selected="true"``,
        but never visible. Callers assert its *attachment*, and the Indexes
        panel's *visibility*.

        The waited-on handle moved from ``toolkit-indexes-accordion`` to
        ``toolkit-indexes-panel`` with the #1616 redesign — see
        :attr:`indexes_panel` for why the panel ROOT is the only honest
        handle for a toolkit with no PgVector/Embedding Model configured.

        Args:
            timeout: Maximum wait time in milliseconds for the Indexes
                side panel to become visible.
        """
        self.indexes_panel.wait_for(state="visible", timeout=timeout)

    def open_test_surface(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Open the standalone Test Toolkit surface from the detail view.

        The #1616 redesign moved the whole TEST SETTINGS surface off the
        detail view and onto its own route,
        ``/toolkits/{tab}/{toolkit_id}/test``. Navigation goes through the
        product's OWN control — the action-bar :attr:`test_button` — rather
        than forcing the URL, so the navigation itself stays exercised
        instead of substituted.

        Args:
            timeout: Maximum wait time in milliseconds, applied both to the
                button becoming visible and to the URL transition.
        """
        self.test_button.wait_for(state="visible", timeout=timeout)
        self.test_button.click()
        self.page.wait_for_url(
            re.compile(r".*/toolkits/[^/]+/\d+/test"), timeout=timeout
        )
        logger.info("Opened the Test Toolkit surface")

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
    # Credential Configuration dropdown (CredentialsSelect.jsx)
    # ------------------------------------------------------------------

    @staticmethod
    def _create_option_value(private: bool) -> str:
        """Return the app's own JSON-encoded select value for a CREATE option.

        Mirrors ``CredentialsSelect.jsx``'s ``createActionToSelectValue()``
        exactly (key order ``kind`` then ``private``, compact separators —
        matching JS's ``JSON.stringify`` output, no spaces).
        """
        return json.dumps({"kind": "create_action", "private": bool(private)}, separators=(",", ":"))

    @staticmethod
    def _saved_option_value(elitea_title: str, private: bool) -> str:
        """Return the app's own JSON-encoded select value for a saved-credential option.

        Mirrors ``CredentialsSelect.jsx``'s ``savedRowToSelectValue()``
        exactly (key order ``kind``, ``elitea_title``, ``private``).
        """
        return json.dumps(
            {"kind": "saved", "elitea_title": elitea_title, "private": bool(private)},
            separators=(",", ":"),
        )

    def credential_select_trigger(self, credential_type: str) -> Locator:
        """Return the Configuration dropdown's trigger (combobox) locator for *credential_type*."""
        return self.page.locator(self.CREDENTIAL_SELECT_TRIGGER.format(credential_type))

    def open_credential_dropdown(self, credential_type: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the Configuration dropdown trigger for *credential_type* to open it.

        Args:
            credential_type: The credential type slug (e.g. ``"github"``).
            timeout: Maximum wait time in milliseconds for the trigger to
                become visible before clicking.
        """
        trigger = self.credential_select_trigger(credential_type)
        trigger.wait_for(state="visible", timeout=timeout)
        trigger.click()
        logger.info("Opened the Configuration dropdown for type=%s", credential_type)

    def get_select_group_header(self, title: str) -> Locator:
        """Return the group-header Locator for *title* (e.g. ``"Create"``)."""
        return self.page.locator(self.SELECT_GROUP_HEADER.format(title))

    def get_create_option(self, private: bool) -> Locator:
        """Return the CREATE-section option Locator for the private/project variant."""
        return self.page.locator(self.SELECT_OPTION.format(self._create_option_value(private)))

    def click_create_option(self, private: bool, timeout: int = UI_ELEMENT_TIMEOUT) -> Page:
        """Click a CREATE-section option and return the new tab ("Page") it opens.

        ``CredentialsSelect.jsx``'s ``createSelectHandler`` always opens the
        create-credential form via ``window.open(..., '_blank', ...)``, so
        every CREATE-action click spawns a new browser tab.

        Args:
            private: ``True`` for "New private {type} credentials", ``False``
                for "New project {type} credentials".
            timeout: Maximum wait time in milliseconds for the option to
                become visible before clicking.
        """
        option = self.get_create_option(private)
        option.wait_for(state="visible", timeout=timeout)
        with self.page.context.expect_page() as new_page_info:
            option.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        logger.info("Clicked CREATE option (private=%s) — new tab: %s", private, new_page.url)
        return new_page

    def get_saved_option(self, elitea_title: str, private: bool) -> Locator:
        """Return the Saved-Credentials option Locator matching *elitea_title*/*private*."""
        return self.page.locator(self.SELECT_OPTION.format(self._saved_option_value(elitea_title, private)))

    def select_saved_credential(
        self, elitea_title: str, private: bool, timeout: int = UI_ELEMENT_TIMEOUT
    ) -> None:
        """Click the Saved-Credentials option matching *elitea_title*/*private*.

        Args:
            elitea_title: The credential's ``elitea_title`` (matches the
                option's encoded select value).
            private: Whether the credential is private-scoped.
            timeout: Maximum wait time in milliseconds for the option to
                become visible before clicking.
        """
        option = self.get_saved_option(elitea_title, private)
        option.wait_for(state="visible", timeout=timeout)
        option.click()
        logger.info("Selected saved credential elitea_title=%s private=%s", elitea_title, private)

    def click_refresh_configurations(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the "Refresh the configurations" button and wait for network to settle."""
        self.credential_select_refresh_button.wait_for(state="visible", timeout=timeout)
        self.credential_select_refresh_button.click()
        self.wait_for_network(timeout=timeout)
        logger.info("Clicked 'Refresh the configurations'")

    def get_credential_select_text(self, credential_type: str) -> str:
        """Return the Configuration dropdown trigger's current displayed text."""
        return self.credential_select_trigger(credential_type).text_content() or ""

    def is_credential_select_mismatched(self, credential_type: str) -> bool:
        """Return whether the Configuration dropdown trigger is in the
        red/error mismatched-credential state (``aria-invalid="true"``).
        """
        return self.credential_select_trigger(credential_type).get_attribute("aria-invalid") == "true"
