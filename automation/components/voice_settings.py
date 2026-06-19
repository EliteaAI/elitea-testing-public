"""Voice Settings dialog component for TTS configuration.

Provides helpers for interacting with the Voice Settings modal dialog
that appears from:
1. Chat TTS controls (gear icon while audio is playing)
2. User Settings > Personalization > Voice Personalization section

The dialog contains:
- Voice dropdown (e.g., 'Shimmer', 'Alloy', etc.)
- Speed slider (0.5x - 2x)
- Volume slider (Mute - 100%)
- Cancel and Apply buttons
"""

import logging
from playwright.sync_api import Locator, Page

logger = logging.getLogger("elitea.components.voice_settings")


class VoiceSettingsDialog:
    """Helpers for the Voice Settings modal dialog.

    Usage::

        from components.voice_settings import VoiceSettingsDialog

        dialog = VoiceSettingsDialog.wait_for(page)
        VoiceSettingsDialog.select_voice(dialog, page, "Alloy")
        VoiceSettingsDialog.set_speed(dialog, page, 1.5)
        VoiceSettingsDialog.click_apply(dialog)

    LOCATORS:
        Dialog: h2#variables-dialog-title (ancestor [role="dialog"])
        Voice dropdown: #simple-select-Voice
        Speed slider: input[aria-valuemin="0.5"][aria-valuemax="2"]
        Volume slider: input[aria-valuemin="0"][aria-valuemax="1"]
        Cancel/Apply: .MuiDialogActions-root button
    """

    DIALOG_SELECTOR = '[role="dialog"]:has(h2#variables-dialog-title)'

    @staticmethod
    def wait_for(page: Page, timeout: int = 5000) -> Locator:
        """Wait for the Voice Settings dialog to become visible.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.

        Returns:
            Locator pointing to the dialog element.
        """
        dialog = page.locator(VoiceSettingsDialog.DIALOG_SELECTOR)
        dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Voice Settings dialog opened")
        return dialog

    @staticmethod
    def is_open(page: Page) -> bool:
        """Check if the Voice Settings dialog is currently open.

        Args:
            page: Playwright Page instance.

        Returns:
            True if dialog is visible, False otherwise.
        """
        dialog = page.locator(VoiceSettingsDialog.DIALOG_SELECTOR)
        return dialog.count() > 0 and dialog.first.is_visible()

    @staticmethod
    def get_current_voice(dialog: Locator) -> str:
        """Get the currently selected voice name from the dropdown.

        Args:
            dialog: Locator of the Voice Settings dialog.

        Returns:
            Voice name (e.g., 'Shimmer', 'Fable').
        """
        voice_text_el = dialog.locator('#simple-select-Voice .MuiTypography-labelMedium')
        if voice_text_el.count() > 0:
            voice_text = voice_text_el.text_content() or ""
        else:
            voice_dropdown = dialog.locator('#simple-select-Voice')
            voice_text = voice_dropdown.text_content() or ""
        logger.info("Current voice: %s", voice_text.strip())
        return voice_text.strip()

    @staticmethod
    def open_voice_dropdown(dialog: Locator, page: Page, timeout: int = 3000):
        """Open the Voice selection dropdown.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            timeout: Maximum wait time for dropdown to open.
        """
        voice_dropdown = dialog.locator('#simple-select-Voice')
        voice_dropdown.click()
        page.locator('[role="listbox"]').wait_for(state="visible", timeout=timeout)
        logger.info("Voice dropdown opened")

    @staticmethod
    def get_available_voices(dialog: Locator, page: Page) -> list[str]:
        """Get list of available voice options from the dropdown.

        Opens the dropdown, collects voice names, then closes it.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.

        Returns:
            List of voice names available for selection.
        """
        VoiceSettingsDialog.open_voice_dropdown(dialog, page)
        options = page.locator('[role="listbox"] [role="option"]')
        voices = []
        for i in range(options.count()):
            text = options.nth(i).text_content()
            if text:
                voices.append(text.strip())
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        logger.info("Available voices: %s", voices)
        return voices

    @staticmethod
    def select_voice(dialog: Locator, page: Page, voice_name: str, timeout: int = 3000):
        """Select a voice from the dropdown.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            voice_name: Name of the voice to select (e.g., 'Fable').
            timeout: Maximum wait time in milliseconds.
        """
        VoiceSettingsDialog.open_voice_dropdown(dialog, page, timeout=timeout)
        option = page.locator(f'[role="listbox"] [role="option"]:has-text("{voice_name}")')
        option.click()
        page.wait_for_timeout(300)
        logger.info("Selected voice: %s", voice_name)

    @staticmethod
    def get_speed_value(dialog: Locator) -> float:
        """Get the current speed slider value.

        The speed slider shows values like '0.5x', '1x', '2x'.

        Args:
            dialog: Locator of the Voice Settings dialog.

        Returns:
            Speed value as float (e.g., 0.5, 1.0, 2.0).
        """
        speed_slider = dialog.locator('input[aria-valuemin="0.5"][aria-valuemax="2"]')
        value = speed_slider.get_attribute("aria-valuenow")
        speed = float(value) if value else 1.0
        logger.info("Current speed: %sx", speed)
        return speed

    @staticmethod
    def set_speed(dialog: Locator, page: Page, speed: float):
        """Set the speed slider to a specific value.

        Uses keyboard navigation for precise control:
        - Right arrow increases speed by 0.1
        - Left arrow decreases speed by 0.1

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            speed: Target speed value (0.5 to 2.0).
        """
        speed_input = dialog.locator('input[aria-valuemin="0.5"][aria-valuemax="2"]')
        current = float(speed_input.get_attribute("aria-valuenow") or 1.0)

        speed_thumb = speed_input.locator("xpath=ancestor::span[contains(@class, 'MuiSlider-thumb')]")
        speed_thumb.click()

        steps_needed = int(round((speed - current) / 0.1))
        key = "ArrowRight" if steps_needed > 0 else "ArrowLeft"
        for _ in range(abs(steps_needed)):
            page.keyboard.press(key)
            page.wait_for_timeout(50)

        logger.info("Set speed to: %sx", speed)

    @staticmethod
    def set_speed_by_position(dialog: Locator, page: Page, position: str):
        """Set speed slider to a named position.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            position: 'min' (0.5x), 'center' (1x), or 'max' (2x).
        """
        speed_map = {"min": 0.5, "center": 1.0, "max": 2.0}
        target = speed_map.get(position, 1.0)
        VoiceSettingsDialog.set_speed(dialog, page, target)

    @staticmethod
    def get_volume_value(dialog: Locator) -> int:
        """Get the current volume slider value as percentage.

        Note: Slider internally uses 0-1 (aria-valuenow), but UI displays
        percentages (Mute, 50%, 100%). This method returns percentage for
        user-friendly assertions.

        Args:
            dialog: Locator of the Voice Settings dialog.

        Returns:
            Volume as percentage (0-100).
        """
        volume_input = dialog.locator('input[aria-valuemin="0"][aria-valuemax="1"]')
        value = volume_input.get_attribute("aria-valuenow")
        raw_volume = float(value) if value else 1.0
        volume_percent = int(round(raw_volume * 100))
        logger.info("Current volume: %d%%", volume_percent)
        return volume_percent

    @staticmethod
    def set_volume(dialog: Locator, page: Page, volume_percent: int):
        """Set the volume slider to a specific percentage.

        Note: Slider internally uses 0-1 with step 0.05, but this method
        accepts percentage (0-100) for user-friendly API.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            volume_percent: Target volume percentage (0 to 100).
        """
        volume_input = dialog.locator('input[aria-valuemin="0"][aria-valuemax="1"]')
        current_raw = float(volume_input.get_attribute("aria-valuenow") or 1.0)
        target_raw = volume_percent / 100.0

        volume_thumb = volume_input.locator("xpath=ancestor::span[contains(@class, 'MuiSlider-thumb')]")
        volume_thumb.click()

        steps_needed = int(round((target_raw - current_raw) / 0.05))
        key = "ArrowRight" if steps_needed > 0 else "ArrowLeft"
        for _ in range(abs(steps_needed)):
            page.keyboard.press(key)
            page.wait_for_timeout(10)

        logger.info("Set volume to: %d%%", volume_percent)

    @staticmethod
    def set_volume_by_position(dialog: Locator, page: Page, position: str):
        """Set volume slider to a named position.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
            position: 'mute' (0%), 'half' (50%), or 'full' (100%).
        """
        volume_map = {"mute": 0, "half": 50, "full": 100}
        target = volume_map.get(position, 100)
        VoiceSettingsDialog.set_volume(dialog, page, target)

    @staticmethod
    def is_cancel_button_visible(dialog: Locator) -> bool:
        """Check if Cancel button is visible.

        Args:
            dialog: Locator of the Voice Settings dialog.

        Returns:
            True if Cancel button is visible.
        """
        return dialog.locator('.MuiDialogActions-root button:has-text("Cancel")').is_visible()

    @staticmethod
    def is_apply_button_visible(dialog: Locator) -> bool:
        """Check if Apply button is visible.

        Args:
            dialog: Locator of the Voice Settings dialog.

        Returns:
            True if Apply button is visible.
        """
        return dialog.locator('.MuiDialogActions-root button:has-text("Apply")').is_visible()

    @staticmethod
    def click_apply(dialog: Locator):
        """Click the Apply button to save changes.

        Args:
            dialog: Locator of the Voice Settings dialog.
        """
        dialog.locator('.MuiDialogActions-root button:has-text("Apply")').click()
        logger.info("Clicked Apply button")

    @staticmethod
    def click_cancel(dialog: Locator):
        """Click the Cancel button to discard changes.

        Args:
            dialog: Locator of the Voice Settings dialog.
        """
        dialog.locator('.MuiDialogActions-root button:has-text("Cancel")').click()
        logger.info("Clicked Cancel button")

    @staticmethod
    def close(dialog: Locator, page: Page):
        """Close the dialog via the X button.

        Args:
            dialog: Locator of the Voice Settings dialog.
            page: Playwright Page instance.
        """
        close_btn = dialog.locator('button[aria-label="close"]')
        if close_btn.count() == 0:
            close_btn = dialog.locator('.MuiDialogTitle-root button').first
        close_btn.click()
        page.wait_for_timeout(300)
        logger.info("Closed Voice Settings dialog")

    @staticmethod
    def wait_for_closed(page: Page, timeout: int = 5000):
        """Wait for the Voice Settings dialog to close.

        Args:
            page: Playwright Page instance.
            timeout: Maximum wait time in milliseconds.
        """
        dialog = page.locator(VoiceSettingsDialog.DIALOG_SELECTOR)
        dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("Voice Settings dialog closed")
