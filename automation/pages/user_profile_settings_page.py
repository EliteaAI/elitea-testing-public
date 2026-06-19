"""User Profile Settings page object for Elitea platform.

Handles the /app/user-settings/profile page, specifically:
- Default Context Management section (toggle, max tokens input)

And the /app/user-settings/personalization page:
- Voice Personalization section (voice, speed, volume, preview)

Changes on these pages autosave — there is no explicit Save button.

URL: /app/user-settings/profile, /app/user-settings/personalization
"""

import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.user_profile_settings")


class UserProfileSettingsPage(BasePage):
    """Page object for /app/user-settings/profile.

    Covers the Default Context Management section which contains:
    - A toggle to enable/disable context management for new conversations
    - A numeric input for Max Context Tokens
    - A numeric input for Preserve Recent Messages

    All changes autosave on blur/change — no Save button interaction needed.

    URL: /app/user-settings/profile
    """

    # ------------------------------------------------------------------
    # Default Context Management — toggle
    # LOCATOR NOTE: The switch has an accessible name. No data-testid is
    # present in the frontend, so fallback is the only strategy.
    # ------------------------------------------------------------------

    context_management_toggle = LocatorDescriptor(
        testid="context-management-toggle",
        fallback=lambda page: page.get_by_role(
            "switch", name="Enable context management for new conversations"
        ),
        description=(
            "Toggle switch for 'Enable context management for new conversations' "
            "inside the Default Context Management section"
        ),
    )

    # ------------------------------------------------------------------
    # Default Context Management — Max Context Tokens input
    # LOCATOR NOTE: The textbox has no accessible name. It is the first
    # unnamed textbox inside the region that also contains the label text
    # 'Max Context Tokens'. We scope the locator to the section heading
    # region to avoid matching the Preserve Recent Messages input.
    # ------------------------------------------------------------------

    max_context_tokens_input = LocatorDescriptor(
        testid="max-context-tokens-input",
        fallback=lambda page: page.get_by_role(
            "heading", name="Default Context Management"
        ).locator("..").get_by_role("region").get_by_role("textbox").nth(0),
        description=(
            "Numeric input for Max Context Tokens. "
            "Located as the first textbox inside the Default Context Management region."
        ),
    )

    # ------------------------------------------------------------------
    # Default Context Management — Preserve Recent Messages input
    # ------------------------------------------------------------------

    preserve_recent_messages_input = LocatorDescriptor(
        testid="preserve-recent-messages-input",
        fallback=lambda page: page.get_by_role(
            "heading", name="Default Context Management"
        ).locator("..").get_by_role("region").get_by_role("textbox").nth(1),
        description=(
            "Numeric input for Preserve Recent Messages. "
            "Located as the second textbox inside the Default Context Management region."
        ),
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_profile(self) -> None:
        """Navigate to the user profile settings page and wait until ready.

        Automatically waits for the page heading and context management
        section to be visible before returning.
        """
        self.navigate("/app/user-settings/profile")
        self.wait_for_page_load()
        logger.info("Navigated to user profile settings page")

    def wait_for_page_load(self, timeout: int = 30000) -> None:
        """Wait until the profile settings page is fully loaded.

        The page initially renders with default values (e.g., 64000 for max tokens),
        then fetches user settings and re-renders. We must wait for this second
        render to complete before reading field values.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)

        # Wait for the "Default Context Management" section heading first
        # The toggle is inside an accordion that might need time to expand
        context_heading = self.page.get_by_role("heading", name="Default Context Management")
        context_heading.wait_for(state="visible", timeout=timeout)

        # The accordion should be expanded by default, but give it time to render
        self.page.wait_for_timeout(500)

        # Wait for the context management toggle to be present — it is
        # the key element used by the context management tests.
        self.context_management_toggle.wait_for(state="visible", timeout=timeout)

        # Wait for user settings to load - the page first shows defaults,
        # then re-renders with actual saved values after API response.
        # Use a longer wait to allow for the settings fetch + re-render cycle.
        self.page.wait_for_timeout(1000)
        logger.info("Profile settings page loaded")

    # ------------------------------------------------------------------
    # Context Management helpers
    # ------------------------------------------------------------------

    def is_context_management_enabled(self) -> bool:
        """Return True if the context management toggle is currently ON.

        Uses the ARIA ``checked`` attribute set by MUI Switch.

        Returns:
            True if the switch is checked (context management enabled).
        """
        checked = self.context_management_toggle.is_checked()
        logger.info("Context management enabled: %s", checked)
        return checked

    def enable_context_management(self) -> None:
        """Enable context management if it is not already enabled.

        Clicks the toggle only when it is currently OFF. After clicking,
        waits for the autosave network round-trip to settle.
        """
        if not self.is_context_management_enabled():
            logger.info("Enabling context management toggle")
            self.context_management_toggle.click()
            self.wait_for_autosave()
        else:
            logger.info("Context management already enabled — no action taken")

    def disable_context_management(self) -> None:
        """Disable context management if it is not already disabled.

        Clicks the toggle only when it is currently ON. After clicking,
        waits for the autosave network round-trip to settle.
        """
        if self.is_context_management_enabled():
            logger.info("Disabling context management toggle")
            self.context_management_toggle.click()
            self.wait_for_autosave()
        else:
            logger.info("Context management already disabled — no action taken")

    def get_max_context_tokens(self) -> int:
        """Return the current value of the Max Context Tokens input.

        Returns:
            Current token limit as an integer.

        Raises:
            ValueError: If the field contains a non-numeric value.
        """
        raw = self.max_context_tokens_input.input_value()
        logger.info("Max context tokens raw value: %r", raw)
        return int(raw)

    def set_max_context_tokens(self, value: int) -> None:
        """Set the Max Context Tokens input to *value*.

        Uses keyboard events (click + Ctrl+A + type) instead of fill() to
        correctly trigger React's onChange handler on MUI form fields.
        fill() sets the DOM value directly but React state never updates,
        so the autosave request would not include the new value.

        Args:
            value: New token limit (positive integer).
        """
        logger.info("Setting max context tokens to %d", value)
        field = self.max_context_tokens_input

        # Clear the field and type the new value character by character
        # This approach reliably triggers React's onChange for MUI inputs
        field.click()
        field.fill("")  # Clear existing value
        field.type(str(value), delay=50)  # Type character by character

        # Press Tab to blur and trigger autosave
        field.press("Tab")
        self.page.wait_for_timeout(3000)  # Wait for debounced autosave

        self.wait_for_network(timeout=5000)
        actual = self.get_max_context_tokens()
        if actual != value:
            logger.warning("Max context tokens shows %d after set, expected %d — autosave may be delayed", actual, value)
        logger.info("Max context tokens set to %d", value)

    def wait_for_autosave(self, timeout: int = 5000) -> None:
        """Wait for the autosave network request to complete.

        Profile settings save automatically on change/blur. This method
        waits for network activity to settle after an interaction.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            # networkidle may not fire if the save is purely local state;
            # a short fixed wait is the fallback.
            self.page.wait_for_timeout(1000)
        logger.info("Autosave settled")

    # ------------------------------------------------------------------
    # Voice Personalization section (Personalization page)
    # ------------------------------------------------------------------

    def navigate_to_personalization(self) -> None:
        """Navigate to the Personalization settings page and wait until ready.

        URL: /app/user-settings/personalization
        """
        self.navigate("/app/user-settings/personalization")
        self.wait_for_personalization_load()
        logger.info("Navigated to Personalization settings page")

    def wait_for_personalization_load(self, timeout: int = 15000) -> None:
        """Wait until the Personalization page is fully loaded.

        Waits for the Voice Personalization section heading to be visible.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        self.wait_for_network(timeout=timeout)
        # Use Voice dropdown as anchor - it has unique ID
        voice_dropdown = self.page.locator('#simple-select-Voice')
        voice_dropdown.scroll_into_view_if_needed()
        voice_dropdown.wait_for(state="visible", timeout=timeout)
        self.page.wait_for_timeout(500)
        logger.info("Personalization page loaded")

    def is_voice_personalization_visible(self) -> bool:
        """Check if the Voice Personalization section is visible.

        Returns:
            True if the Voice dropdown is visible.
        """
        voice_dropdown = self.page.locator('#simple-select-Voice')
        return voice_dropdown.count() > 0 and voice_dropdown.first.is_visible()

    def get_voice_personalization_section(self):
        """Get the Voice Personalization section locator.

        Returns:
            Locator for the Voice Personalization section container.
        """
        return self.page.locator('#simple-select-Voice').locator('xpath=ancestor::div[contains(@class, "MuiAccordion-root")]')

    def get_current_voice(self) -> str:
        """Get the currently selected voice in Voice Personalization.

        Returns:
            Voice name (e.g., 'Shimmer').
        """
        voice_text_el = self.page.locator('#simple-select-Voice .MuiTypography-labelMedium')
        if voice_text_el.count() > 0:
            voice_text = voice_text_el.text_content() or ""
        else:
            voice_dropdown = self.page.locator('#simple-select-Voice')
            voice_text = voice_dropdown.text_content() or ""
        logger.info("Current voice: %s", voice_text.strip())
        return voice_text.strip()

    @action("Select voice in Personalization")
    def select_voice(self, voice_name: str, timeout: int = 3000):
        """Select a voice from the Voice dropdown in Personalization section.

        Args:
            voice_name: Name of the voice to select (e.g., 'Alloy').
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Selecting voice: %s", voice_name)
        voice_dropdown = self.page.locator('#simple-select-Voice')
        voice_dropdown.scroll_into_view_if_needed()
        voice_dropdown.click()

        self.page.locator('[role="listbox"]').wait_for(state="visible", timeout=timeout)
        option = self.page.locator(f'[role="option"]:has-text("{voice_name}")')
        option.click()

        self.page.wait_for_timeout(500)
        self.wait_for_autosave()
        logger.info("Voice selected: %s", voice_name)

    def get_available_voices(self) -> list[str]:
        """Get list of available voice options.

        Opens the dropdown, collects voice names, then closes it.

        Returns:
            List of voice names.
        """
        voice_dropdown = self.page.locator('#simple-select-Voice')
        voice_dropdown.scroll_into_view_if_needed()
        voice_dropdown.click()

        self.page.locator('[role="listbox"]').wait_for(state="visible", timeout=3000)
        options = self.page.locator('[role="option"]')
        voices = []
        for i in range(options.count()):
            text = options.nth(i).text_content()
            if text:
                voices.append(text.strip())

        self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(300)
        logger.info("Available voices: %s", voices)
        return voices

    def get_speed_value(self) -> float:
        """Get the current speed slider value.

        Returns:
            Speed value as float (e.g., 0.5, 1.0, 2.0).
        """
        speed_input = self.page.locator('input[aria-valuemin="0.5"][aria-valuemax="2"]')
        speed_input.scroll_into_view_if_needed()
        value = speed_input.get_attribute("aria-valuenow")
        speed = float(value) if value else 1.0
        logger.info("Current speed: %sx", speed)
        return speed

    @action("Set speed in Personalization")
    def set_speed(self, speed: float):
        """Set the speed slider to a specific value.

        Args:
            speed: Target speed value (0.5 to 2.0).
        """
        logger.info("Setting speed to: %sx", speed)
        speed_input = self.page.locator('input[aria-valuemin="0.5"][aria-valuemax="2"]')
        speed_input.scroll_into_view_if_needed()
        current = float(speed_input.get_attribute("aria-valuenow") or 1.0)

        # Click on the thumb to focus
        speed_thumb = speed_input.locator("xpath=ancestor::span[contains(@class, 'MuiSlider-thumb')]")
        speed_thumb.click()

        steps_needed = int(round((speed - current) / 0.1))
        key = "ArrowRight" if steps_needed > 0 else "ArrowLeft"
        for _ in range(abs(steps_needed)):
            self.page.keyboard.press(key)
            self.page.wait_for_timeout(50)

        self.page.keyboard.press("Tab")
        self.wait_for_autosave()
        logger.info("Speed set to: %sx", speed)

    def get_volume_value(self) -> int:
        """Get the current volume slider value.

        Returns:
            Volume as percentage (0-100).
        """
        volume_input = self.page.locator('input[aria-valuemin="0"][aria-valuemax="1"]')
        volume_input.scroll_into_view_if_needed()
        value = volume_input.get_attribute("aria-valuenow")
        raw_volume = float(value) if value else 1.0
        volume_percent = int(round(raw_volume * 100))
        logger.info("Current volume: %d%%", volume_percent)
        return volume_percent

    @action("Set volume in Personalization")
    def set_volume(self, volume_percent: int):
        """Set the volume slider to a specific percentage.

        Args:
            volume_percent: Target volume percentage (0 to 100).
        """
        logger.info("Setting volume to: %d%%", volume_percent)
        volume_input = self.page.locator('input[aria-valuemin="0"][aria-valuemax="1"]')
        volume_input.scroll_into_view_if_needed()
        current_raw = float(volume_input.get_attribute("aria-valuenow") or 1.0)
        target_raw = volume_percent / 100.0

        # Click on the thumb to focus
        volume_thumb = volume_input.locator("xpath=ancestor::span[contains(@class, 'MuiSlider-thumb')]")
        volume_thumb.click()

        steps_needed = int(round((target_raw - current_raw) / 0.05))
        key = "ArrowRight" if steps_needed > 0 else "ArrowLeft"
        for _ in range(abs(steps_needed)):
            self.page.keyboard.press(key)
            self.page.wait_for_timeout(10)

        self.page.keyboard.press("Tab")
        self.wait_for_autosave()
        logger.info("Volume set to: %d%%", volume_percent)

    @action("Click Preview Voice")
    def click_preview_voice(self, timeout: int = 5000):
        """Click the 'Preview Voice' button to hear a sample with current settings.

        This button is only available in the Personalization page, not in the
        Voice Settings dialog accessed from Chat.

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        logger.info("Clicking Preview Voice button")
        preview_btn = self.page.locator('button:has-text("Preview Voice")')
        preview_btn.wait_for(state="visible", timeout=timeout)
        preview_btn.click()
        self.page.wait_for_timeout(500)
        logger.info("Preview Voice clicked")

    def is_preview_voice_button_visible(self) -> bool:
        """Check if the Preview Voice button is visible.

        Returns:
            True if button is visible, False otherwise.
        """
        preview_btn = self.page.locator('button:has-text("Preview Voice")')
        return preview_btn.count() > 0 and preview_btn.first.is_visible()

    def get_voice_personalization_controls(self) -> dict:
        """Get the current state of all Voice Personalization controls.

        Returns:
            Dict with keys: voice, speed, volume
        """
        return {
            "voice": self.get_current_voice(),
            "speed": self.get_speed_value(),
            "volume": self.get_volume_value(),
        }
