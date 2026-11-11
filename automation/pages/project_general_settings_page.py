"""Project General Settings page object (Settings → General).

Covers the Chat configuration section's "Mid-turn input" card — a project-level
toggle that gates the chat interjection queue. The toggle autosaves on change
(formik submit → module_settings PUT); the card is hidden (not disabled) when the
platform tier is blocked or the user lacks project-context permission.

URL: /settings/project-general
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, ScopedLocator
from utils.actions import action

logger = logging.getLogger("elitea.pages.project_general_settings")


class ProjectGeneralSettingsPage(BasePage):
    """Page object for /settings/project-general (Mid-turn input card)."""

    PATH = "/settings/project-general"

    chat_configuration_section = LocatorDescriptor(
        testid="chat-configuration-section",
        description="Chat configuration section container on Settings → General",
    )

    MIDTURN_INPUT_SWITCH = ScopedLocator(
        css='div:has(> div > :text-is("Mid-turn input")) input[role="switch"]',
        description="Mid-turn input card's MUI Switch input, scoped to the card whose title is 'Mid-turn input'",
        suggested_testid="settings-midturn-input-switch",
    )

    default_modules_section = LocatorDescriptor(
        testid="default-modules-section",
        description="Default Modules section (Module / Chats / Agents grid) on Settings → General",
    )

    # Scope MUST be default_modules_section: the separate web-search-section card
    # also carries a 'Web Search' title.
    WEB_SEARCH_MODULE_ROW = ScopedLocator(
        css='div:has(> div > :text-is("Web Search"))',
        description="Web Search row of Default Modules: the box holding title+description and the two switch cells",
        suggested_testid="settings-default-modules-web-search-row",
    )

    WEB_SEARCH_MODULE_SWITCHES = ScopedLocator(
        css='input[role="switch"]',
        description=(
            "The Web Search row's switch inputs, enumerated: DOM order is the column order "
            "(first = Chats, second = Agents); neither carries a label/testid on DEV"
        ),
        suggested_testid="settings-default-modules-web-search-switch",
    )

    WEB_SEARCH_MODULE_DESCRIPTION = ScopedLocator(
        css=':text-is("Allow the LLM to search the Internet, read web pages, and cite its sources.")',
        description="Web Search row description paragraph (the row's only tooltip text in Default Modules)",
        suggested_testid="settings-default-modules-web-search-description",
    )

    COLUMN_HEADER = ScopedLocator(
        css=':text-is("{}")',
        description="Default Modules column header text ('Chats' / 'Agents')",
        suggested_testid="settings-default-modules-column-header-{}",
    )

    @property
    def web_search_row(self):
        """Web Search row inside the Default Modules section."""
        return self.WEB_SEARCH_MODULE_ROW.within(self.default_modules_section)

    @property
    def midturn_input_switch(self):
        """The Mid-turn input switch, resolved inside the Chat configuration section."""
        return self.MIDTURN_INPUT_SWITCH.within(self.chat_configuration_section)

    @action("Open Settings → General")
    def open(self) -> None:
        """Navigate to Settings → General and dismiss the platform announcement dialog (inherited BasePage helpers)."""
        self.navigate(self.PATH)
        self.chat_configuration_section.wait_for(state="visible", timeout=30_000)
        self.dismiss_announcement_dialog_if_present()
        # The dialog can render seconds late: guard every later action on this page.
        self.auto_dismiss_announcement_dialog()

    @action("Read Mid-turn input toggle state")
    def is_midturn_input_enabled(self) -> bool:
        """Return whether the Mid-turn input switch is checked (waits for the card to render)."""
        self.midturn_input_switch.wait_for(state="attached", timeout=30_000)
        return self.midturn_input_switch.is_checked()

    @action("Enable Mid-turn input toggle")
    def enable_midturn_input(self) -> None:
        """Turn the toggle on if it is off; wait for the autosave PUT and the checked state."""
        if self.is_midturn_input_enabled():
            return
        with self.page.expect_response(
            lambda r: "module_settings" in r.url and r.request.method in ("PUT", "POST", "PATCH")
        ) as resp_info:
            self.midturn_input_switch.click()
        assert resp_info.value.ok, f"module_settings autosave failed: {resp_info.value.status}"
        expect(self.midturn_input_switch).to_be_checked()

    # ------------------------------------------------------------------
    # Default Modules → Web Search row
    # ------------------------------------------------------------------

    @action("Open Settings → General (Default Modules)")
    def open_default_modules(self) -> None:
        """Navigate to Settings → General and wait for Default Modules (the Chat configuration card can be absent)."""
        self.navigate(self.PATH)
        self.dismiss_announcement_dialog_if_present()
        self.auto_dismiss_announcement_dialog()
        self.wait_for_default_modules()

    @action("Wait for Default Modules section")
    def wait_for_default_modules(self) -> None:
        """Wait until the Default Modules section and its Web Search row are rendered."""
        self.default_modules_section.wait_for(state="visible", timeout=30_000)
        self.web_search_row.first.wait_for(state="visible", timeout=30_000)

    def is_default_modules_column_header_visible(self, name: str) -> bool:
        """Whether the 'Chats' / 'Agents' column header is visible in Default Modules."""
        return self.COLUMN_HEADER.within(self.default_modules_section, name).first.is_visible()

    @property
    def web_search_description(self):
        """Web Search description paragraph, scoped to its row."""
        return self.WEB_SEARCH_MODULE_DESCRIPTION.within(self.web_search_row)

    def web_search_switches(self) -> list:
        """Web Search row switches in column order [Chats, Agents] (enumerated, not picked)."""
        return self.WEB_SEARCH_MODULE_SWITCHES.within(self.web_search_row).all()

    @action("Set Web Search default for Chats")
    def set_web_search_chats_default(self, enabled: bool) -> None:
        """Set the Chats switch of the Web Search row; autosaves on blur, so blur and await the PUT."""
        chats_switch = self.web_search_switches()[0]
        if chats_switch.is_checked() == enabled:
            return
        chats_switch.click()
        with self.page.expect_response(
            lambda r: "module_settings" in r.url and r.request.method in ("PUT", "POST", "PATCH")
        ) as resp_info:
            self.page.mouse.click(5, 5)  # blur → formik autosave
        assert resp_info.value.ok, f"module_settings autosave failed: {resp_info.value.status}"
        expect(chats_switch).to_be_checked(checked=enabled)
