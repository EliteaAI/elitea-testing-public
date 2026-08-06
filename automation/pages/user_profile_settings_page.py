"""User Profile Settings page object for Elitea platform.

Handles the /settings/memory page, specifically:
- Context Management section (toggle, Max Context Tokens / Preserve Recent
  Messages inputs, Automatic Summarization sub-section)

And the /settings/preferences page:
- Voice Personalization section (voice, speed, volume, preview)

Changes on these pages autosave — there is no explicit Save button.

URL: /settings/memory, /settings/preferences

NOTE: /settings/personalization and /user-settings/profile are STALE routes
that 404 — see navigate_to_profile() and EliteaAI/elitea-testing-public#1238.
"""

import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action

logger = logging.getLogger("elitea.pages.user_profile_settings")


class UserProfileSettingsPage(BasePage):
    """Page object for /settings/memory.

    Covers the Context Management section which contains:
    - A toggle to enable/disable context management for new conversations
    - A numeric input for Max Context Tokens
    - A numeric input for Preserve Recent Messages
    - An Automatic Summarization sub-section (own toggle)

    Context Management is a conditional-unmount block, not a disabled/
    grayed-out one: with the top toggle OFF, the Max Context Tokens input,
    Preserve Recent Messages input, Context Editing toggle, and the entire
    Automatic Summarization sub-section are removed from the DOM entirely
    (`{isEnabled && (...)}` in `MemoryContextManagement.jsx`), and reappear
    with prior values intact when re-enabled.

    All changes autosave on click/change — no Save button interaction needed.

    URL: /settings/memory
    """

    # ------------------------------------------------------------------
    # Context Management — section container
    # ------------------------------------------------------------------

    context_management_section = LocatorDescriptor(
        testid="context-management-section",
        description="Container for the Context Management accordion section on /settings/memory",
    )

    # ------------------------------------------------------------------
    # Context Management — toggle
    # ------------------------------------------------------------------

    context_management_toggle = LocatorDescriptor(
        testid="context-management-toggle",
        description=(
            "Toggle switch for 'Enable context management for new conversations' "
            "inside the Context Management section"
        ),
    )

    # ------------------------------------------------------------------
    # Context Management — Max Context Tokens input
    # ------------------------------------------------------------------

    max_context_tokens_input = LocatorDescriptor(
        testid="max-context-tokens-input",
        description="Numeric input for Max Context Tokens.",
    )

    # ------------------------------------------------------------------
    # Context Management — Preserve Recent Messages input
    # ------------------------------------------------------------------

    preserve_recent_messages_input = LocatorDescriptor(
        testid="preserve-recent-messages-input",
        description="Numeric input for Preserve Recent Messages.",
    )

    # ------------------------------------------------------------------
    # Context Management — Automatic Summarization sub-section toggle
    # ------------------------------------------------------------------

    automatic_summarization_toggle = LocatorDescriptor(
        testid="automatic-summarization-toggle",
        description=(
            "Toggle switch for the Automatic Summarization sub-section "
            "(MemorySummarization.jsx), nested inside Context Management"
        ),
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate_to_profile(self) -> None:
        """Navigate to the Context Management settings page and wait until ready.

        Context Management now lives at /settings/memory. The former routes
        (/settings/personalization, /user-settings/profile) 404 — the section
        was relocated without updating case text / this method's old route
        (see EliteaAI/elitea-testing-public#1238).

        Automatically waits for the context management section to be visible
        before returning.
        """
        self.navigate("/settings/memory")
        self.wait_for_page_load()
        logger.info("Navigated to Context Management settings page (/settings/memory)")

    def wait_for_page_load(self, timeout: int = 60000) -> None:
        """Wait until the profile settings page is fully loaded with API data.

        The page initially renders with default values (e.g., 64000 for max tokens),
        then fetches user settings and re-renders. We must wait for this second
        render to complete before reading field values.

        The /settings/memory page has a persistent WebSocket connection
        (socket.io) that prevents networkidle from being reached, so the
        networkidle wait is best-effort (failure is tolerated).

        After DOM elements are visible, we poll the max-context-tokens-input until
        its value is stable for two consecutive reads 500ms apart. This guards
        against reading the form before the author API response has updated the
        Formik state (which can lag especially when the backend returns transient
        503s on reload and retries). If Context Management is currently OFF for
        this account, the input is conditionally unmounted (not merely hidden) —
        the poll is skipped in that case rather than spinning for the full
        timeout waiting on a value that will never appear.

        Args:
            timeout: Maximum wait time in milliseconds (default raised to 60s to
                     allow for backend 503 retry cycles).
        """
        import time as _time

        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            logger.debug("wait_for_page_load: networkidle not reached — continuing")

        # Wait for the Context Management section accordion container.
        # The accordion title is not a semantic heading — use its data-testid instead.
        self.context_management_section.wait_for(state="visible", timeout=timeout)

        # The accordion should be expanded by default, but give it time to render
        self.page.wait_for_timeout(500)

        # Wait for the context management toggle to be present — it is
        # the key element used by the context management tests.
        self.context_management_toggle.wait_for(state="visible", timeout=timeout)

        if self.max_context_tokens_input.count() == 0:
            logger.info(
                "wait_for_page_load: Context Management is OFF for this account "
                "(Max Context Tokens input not mounted) — skipping value-stabilization poll"
            )
            logger.info("Profile settings page loaded")
            return

        # Poll max-context-tokens-input until the value is stable.
        # The form first shows the Formik default (64000), then updates when the
        # author API call completes.  Two consecutive identical reads separated by
        # 500ms indicate the API data has been applied and the form has settled.
        deadline = _time.monotonic() + timeout / 1000.0
        previous = None
        while _time.monotonic() < deadline:
            try:
                raw = self.max_context_tokens_input.input_value()
                current = int(raw) if raw.strip() else None
            except Exception:
                current = None

            if current is not None and current == previous:
                logger.debug("wait_for_page_load: value stable at %d", current)
                break

            previous = current
            self.page.wait_for_timeout(500)
        else:
            logger.warning("wait_for_page_load: value did not stabilise within timeout — proceeding anyway")

        logger.info("Profile settings page loaded")

    # ------------------------------------------------------------------
    # Context Management helpers
    # ------------------------------------------------------------------

    def is_context_management_enabled(self) -> bool:
        """Return True if the context management toggle is currently ON.

        Same shape as ``ArtifactsPage.is_file_checkbox_checked`` /
        ``NotificationCenterPage.is_notification_checkbox_checked``: the
        ``data-testid`` lands on the MUI ``SwitchBase`` root span (confirmed
        live — ``<span class="... Mui-checked ..." data-testid="context-
        management-toggle"><input type="checkbox" role="switch" .../></span>``),
        not the nested ``<input>``, so Playwright's ``is_checked()`` raises
        "Not a checkbox or radio button" on it — read the ``Mui-checked``
        class instead.

        Returns:
            True if the switch is checked (context management enabled).
        """
        class_attr = self.context_management_toggle.get_attribute("class") or ""
        checked = "Mui-checked" in class_attr
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

    def get_preserve_recent_messages(self) -> int:
        """Return the current value of the Preserve Recent Messages input.

        Returns:
            Current preserve-recent-messages count as an integer.

        Raises:
            ValueError: If the field contains a non-numeric value.
        """
        raw = self.preserve_recent_messages_input.input_value()
        logger.info("Preserve recent messages raw value: %r", raw)
        return int(raw)

    def are_context_fields_mounted(self) -> bool:
        """Return True if Max Context Tokens and Preserve Recent Messages
        inputs are present in the DOM.

        Context Management OFF conditionally UNMOUNTS these fields (and the
        Automatic Summarization sub-section) rather than disabling them —
        see the class docstring. Use ``count() > 0`` (presence), not
        visibility, since an unmounted element also fails a visibility check
        but for a different reason.

        Returns:
            True if both inputs are present in the DOM.
        """
        return self.max_context_tokens_input.count() > 0 and self.preserve_recent_messages_input.count() > 0

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

        # Use wait_for_autosave which tolerates the persistent WebSocket on
        # /settings/memory preventing networkidle from being reached.
        self.wait_for_autosave(timeout=5000)
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
        """Navigate to the Personalization settings page and wait until ready."""
        self.navigate("/settings/preferences")
        self.wait_for_personalization_load()
        logger.info("Navigated to Personalization settings page")

    def wait_for_personalization_load(self, timeout: int = 15000) -> None:
        """Wait until the Personalization page is fully loaded.

        Waits for the Voice Personalization section to be visible and DOM-stable.
        The section may re-render as TTS voices are fetched from the API, so we
        wait for the section container (data-testid) and then for the voice
        dropdown to be stable before returning.

        The /settings/personalization page has a persistent WebSocket connection
        that prevents networkidle from being reached, so the networkidle wait is
        best-effort (failure is tolerated).

        Args:
            timeout: Maximum wait time in milliseconds.
        """
        # networkidle is best-effort: /settings/personalization has a persistent
        # WebSocket that keeps the network active.  Failure here is fine because
        # the element-level waits below are the real readiness signals.
        try:
            self.wait_for_network(timeout=timeout)
        except Exception:
            logger.debug("wait_for_personalization_load: networkidle not reached — continuing")
        # Wait for the Voice Personalization section container first
        section = self.page.get_by_test_id("voice-personalization-section")
        section.wait_for(state="visible", timeout=timeout)
        # Wait for the Voice dropdown to appear (may be absent until voices load)
        voice_dropdown = self.page.locator('#simple-select-Voice')
        voice_dropdown.wait_for(state="visible", timeout=timeout)
        # Allow extra time for React to finish re-rendering after voices are fetched
        self.page.wait_for_timeout(1000)
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

    def get_current_voice(self, timeout: int = 5000) -> str:
        """Get the currently selected voice in Voice Personalization.

        Waits up to *timeout* ms for voices to load (MUI Select renders a
        zero-width-space placeholder until the async voice list arrives, which
        makes text_content() return '\u200b').  Falls back to an empty string
        when voices never populate within the timeout.

        Returns:
            Voice name (e.g., 'Shimmer'), or '' if voices are not yet loaded.
        """
        import time as _time
        deadline = _time.monotonic() + timeout / 1000.0
        while True:
            voice_text_el = self.page.locator('#simple-select-Voice .MuiTypography-labelMedium')
            if voice_text_el.count() > 0:
                voice_text = (voice_text_el.text_content() or "").replace('\u200b', '').strip()
                if voice_text:
                    logger.info("Current voice (labelMedium): %s", voice_text)
                    return voice_text
            voice_dropdown = self.page.locator('#simple-select-Voice')
            if voice_dropdown.count() > 0:
                raw = (voice_dropdown.text_content() or "").replace('\u200b', '').strip()
                if raw:
                    logger.info("Current voice (textContent): %s", raw)
                    return raw
                # Element exists but shows only \u200b: the MUI Select renders its
                # empty-value state as a zero-width space (not "Default" text).
                # #simple-select-Voice only appears in the DOM when voiceOptions.length>0
                # (see VoiceConfigControls.jsx conditional render), so the element
                # being present means voices ARE loaded — the user simply has no voice
                # configured.  Return "Default" as a truthy sentinel so callers can
                # proceed (assert passes, select_voice skips gracefully via its guard).
                logger.info("get_current_voice: element present with \\u200b only → no voice selected, returning 'Default'")
                return "Default"
            # Element not in DOM yet: voices still loading — wait and retry
            if _time.monotonic() >= deadline:
                logger.warning("get_current_voice: voice dropdown did not appear within %dms", timeout)
                return ''
            self.page.wait_for_timeout(300)

    @action("Select voice in Personalization")
    def select_voice(self, voice_name: str, timeout: int = 5000):
        """Select a voice from the Voice dropdown in Personalization section.

        Uses Locator.click() directly (no scroll_into_view_if_needed) to avoid
        stale ElementHandle errors when React re-renders the voice list after
        the TTS voices API response arrives.

        Uses get_by_test_id("select-option-{value}") for stable testid-based matching.
        The testid is set in SingleSelectMenuItem.jsx as "select-option-{option.value}".
        For TTS voices the value equals the lowercase voice name (e.g. "alloy" for "Alloy").

        Args:
            voice_name: Name of the voice to select (e.g., 'Alloy').
            timeout: Maximum wait time in milliseconds.
        """
        # Guard: skip restore if voice_name is empty, only zero-width space, or the
        # MUI emptyPlaceholder text "Default" (which is not a real selectable option).
        effective_name = voice_name.replace('\u200b', '').strip() if voice_name else ''
        if not effective_name or effective_name.lower() == 'default':
            logger.info("select_voice: '%s' is not a real selectable voice, skipping", effective_name or '(empty)')
            return

        logger.info("Selecting voice: %s", effective_name)
        voice_dropdown = self.page.locator('#simple-select-Voice')
        # click() auto-scrolls and retries on stale elements; do NOT call
        # scroll_into_view_if_needed() first because that resolves to an
        # ElementHandle that can become detached when React re-renders.
        voice_dropdown.click(timeout=timeout)

        self.page.locator('[role="listbox"]').wait_for(state="visible", timeout=timeout)
        # Use data-testid locator for stability; voice option testids are set
        # as "select-option-{value}" in SingleSelectMenuItem.jsx.
        # For TTS voices value == name.lower() (e.g. "Alloy" → "select-option-alloy").
        option = self.page.get_by_test_id(f"select-option-{effective_name.lower()}")
        option.click()

        self.page.wait_for_timeout(500)
        self.wait_for_autosave()
        logger.info("Voice selected: %s", effective_name)

    def get_available_voices(self) -> list[str]:
        """Get list of available voice options.

        Opens the dropdown, collects voice names, then closes it.
        Uses Locator.click() directly to avoid stale ElementHandle errors
        caused by React re-renders.

        Filters out empty strings and MUI zero-width-space (\u200b) placeholders
        that appear in the text_content() of every option element.

        Returns:
            List of voice names (non-empty display labels).
        """
        voice_dropdown = self.page.locator('#simple-select-Voice')
        # click() auto-scrolls and retries on stale elements
        voice_dropdown.click(timeout=5000)

        self.page.locator('[role="listbox"]').wait_for(state="visible", timeout=5000)
        options = self.page.locator('[role="option"]')
        voices = []
        for i in range(options.count()):
            raw = options.nth(i).text_content() or ""
            text = raw.replace('\u200b', '').strip()
            if text:
                voices.append(text)

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

    def _get_voice_section(self):
        """Get the Voice Personalization section container.

        Returns:
            Locator scoped to the Voice Personalization accordion section.
        """
        return self.page.locator('#simple-select-Voice').locator(
            'xpath=ancestor::div[contains(@class, "MuiAccordion-root")]'
        )

    def get_volume_value(self) -> int:
        """Get the current volume slider value.

        Returns:
            Volume as percentage (0-100).
        """
        voice_section = self._get_voice_section()
        volume_input = voice_section.locator('input[aria-valuemin="0"][aria-valuemax="1"]').first
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
        voice_section = self._get_voice_section()
        volume_input = voice_section.locator('input[aria-valuemin="0"][aria-valuemax="1"]').first
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
        preview_btn = self.page.get_by_test_id("voice-preview-button")
        preview_btn.wait_for(state="visible", timeout=timeout)
        preview_btn.click()
        self.page.wait_for_timeout(500)
        logger.info("Preview Voice clicked")

    def is_preview_voice_button_visible(self) -> bool:
        """Check if the Preview Voice button is visible.

        Returns:
            True if button is visible, False otherwise.
        """
        preview_btn = self.page.get_by_test_id("voice-preview-button")
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
