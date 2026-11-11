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
