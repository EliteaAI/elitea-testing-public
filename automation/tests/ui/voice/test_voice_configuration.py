"""UI Tests for Voice Configuration Settings (Enhancement #5010).

Tests the Voice Configuration / Text-to-Speech (TTS) settings feature.
Each test corresponds to one manual test case from OneTest TMS.

Test Cases:
    test_voice_selection_from_chat (TC1) - Voice dropdown, Apply/Cancel behavior
    test_speed_and_volume_controls (TC2) - Slider adjustments
    test_voice_settings_sync (TC3) - Personalization → Chat synchronization
    test_voice_preview_personalization (TC4) - Preview Voice in Personalization

Markers:
    - ui: requires browser
    - voice: voice configuration tests
    - p1: high priority

Usage:
    cd automation
    pytest tests/ui/voice/test_voice_configuration.py -v
    pytest tests/ui/voice/ -v -m voice

Related:
    - Enhancement: https://github.com/EliteaAI/elitea_issues/issues/5010
    - OneTest TMS: enhancement:5010 tag
"""

import logging
import re

import pytest
from pages.chat_page import ChatPage
from pages.user_profile_settings_page import UserProfileSettingsPage
from components.voice_settings import VoiceSettingsDialog
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.voice]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 60_000
TTS_TIMEOUT = 10_000
UI_ELEMENT_TIMEOUT = 5_000
NAVIGATION_TIMEOUT = 15_000


def approx_equal(actual: float, expected: float, tolerance: float = 0.05) -> bool:
    """Check if two floats are approximately equal within tolerance."""
    return abs(actual - expected) <= tolerance


def capture_conversation_id(page) -> str | None:
    """Extract conversation ID from current URL.

    Returns:
        Conversation ID as string, or None if not found.
    """
    match = re.search(r"/app/chat/(\d+)", page.url)
    return match.group(1) if match else None


class TestVoiceConfiguration:
    """Voice Configuration Settings tests matching manual test cases."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1315_apply-saves-and-cancel-discards-voice-settings-changes.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1312_voice-settings-dialog-opens-and-displays-all-controls-including-voice.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_voice_selection_from_chat(self, page, conversation_api):
        """TC1: Voice Selection via TTS Controls in Chat.
        TC-1918, TC-1915
        Steps:
            1. Navigate to Chat, send a message, wait for AI response
            2. Click 'Read out' (speaker) icon on AI response
            3. Click gear/settings icon in TTS control bar
            4. Inspect all dialog elements (Voice, Speed, Volume, Cancel, Apply)
            5. Click Voice dropdown - verify non-empty list
            6. Select a voice different from current
            7. Click Apply - dialog closes, voice saved
            8. Re-open Voice Settings - verify voice persisted
            9. Change voice again, click Cancel - verify reverts to applied voice
        """
        conv_id = None
        try:
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)
            conv_id = capture_conversation_id(page)

            chat.send_message("Tell me about weather in spring. 2-3 sentences.", use_enter=True)
            chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            if not conv_id:
                conv_id = capture_conversation_id(page)

            # Step 2-3: Click Read out, then settings
            chat.click_read_out(message_index=-1, timeout=TTS_TIMEOUT)
            chat.wait_for_tts_controls(timeout=TTS_TIMEOUT)
            dialog = chat.open_voice_settings_from_tts(timeout=UI_ELEMENT_TIMEOUT)

            # Step 4: Inspect all dialog elements
            assert VoiceSettingsDialog.is_open(page), "Voice Settings dialog should be open"

            current_voice = VoiceSettingsDialog.get_current_voice(dialog)
            assert current_voice, "Voice dropdown should show a selected voice"

            speed = VoiceSettingsDialog.get_speed_value(dialog)
            assert 0.5 <= speed <= 2.0, f"Speed should be between 0.5x-2x, got {speed}x"

            volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert 0 <= volume <= 100, f"Volume should be between 0-100%, got {volume}%"

            assert VoiceSettingsDialog.is_cancel_button_visible(dialog), "Cancel button should be visible"
            assert VoiceSettingsDialog.is_apply_button_visible(dialog), "Apply button should be visible"

            # Step 5: Click Voice dropdown - verify non-empty list
            voices = VoiceSettingsDialog.get_available_voices(dialog, page)
            assert len(voices) > 0, "Voice dropdown should have options"

            # Step 6: Select a different voice
            original_voice = VoiceSettingsDialog.get_current_voice(dialog)
            new_voice = next((v for v in voices if v != original_voice), voices[0])
            VoiceSettingsDialog.select_voice(dialog, page, new_voice)

            selected_voice = VoiceSettingsDialog.get_current_voice(dialog)
            assert selected_voice == new_voice, f"Selected voice should be {new_voice}"

            # Step 7: Click Apply
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Step 8: Re-open Voice Settings - verify voice persisted
            page.wait_for_timeout(1000)
            dialog = chat.open_voice_settings_from_tts(timeout=UI_ELEMENT_TIMEOUT)

            persisted_voice = VoiceSettingsDialog.get_current_voice(dialog)
            assert persisted_voice == new_voice, (
                f"Voice should persist as '{new_voice}' after Apply, got '{persisted_voice}'"
            )

            # Step 9: Change voice, click Cancel - verify reverts
            another_voice = next((v for v in voices if v != new_voice), voices[0])
            VoiceSettingsDialog.select_voice(dialog, page, another_voice)
            VoiceSettingsDialog.click_cancel(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            page.wait_for_timeout(1000)
            dialog = chat.open_voice_settings_from_tts(timeout=UI_ELEMENT_TIMEOUT)

            reverted_voice = VoiceSettingsDialog.get_current_voice(dialog)
            assert reverted_voice == new_voice, (
                f"Voice should revert to '{new_voice}' after Cancel, got '{reverted_voice}'"
            )

            VoiceSettingsDialog.click_cancel(dialog)

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as e:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, e)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1313_voice-settings-dialog-speed-and-volume-sliders-adjust-playback.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_speed_and_volume_controls(self, page, conversation_api):
        """TC2: Speed and Volume Slider Adjustments.
        TC-1917
        Steps:
            1. Open Voice Settings - verify defaults (Speed 1x, Volume 100%)
            2. Set Speed to 0.5x, Apply, reopen - verify persisted, then set to 2x
            3. Apply, reopen - verify 2x persisted, then set to 1x
            4. Apply, reopen - verify 1x persisted, then set Volume to Mute
            5. Apply, reopen - verify 0% persisted, then set to 50%
            6. Apply, reopen - verify ~50% persisted, then set to 100%
            7. Apply, reopen - verify 100% persisted
        """
        conv_id = None
        try:
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)
            conv_id = capture_conversation_id(page)

            chat.send_message("Hello, how are you today?", use_enter=True)
            chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            if not conv_id:
                conv_id = capture_conversation_id(page)

            # Step 1: Open Voice Settings - verify defaults
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            speed = VoiceSettingsDialog.get_speed_value(dialog)
            volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert approx_equal(speed, 1.0), f"Default speed should be 1x, got {speed}x"
            assert volume == 100, f"Default volume should be 100%, got {volume}%"

            # Step 2: Set Speed to 0.5x, Apply
            VoiceSettingsDialog.set_speed_by_position(dialog, page, "min")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify 0.5x persisted, then set to 2x
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            speed = VoiceSettingsDialog.get_speed_value(dialog)
            assert approx_equal(speed, 0.5), f"Speed should persist as 0.5x after Apply, got {speed}x"

            # Step 3: Set Speed to 2x, Apply
            VoiceSettingsDialog.set_speed_by_position(dialog, page, "max")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify 2x persisted, then set to 1x
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            speed = VoiceSettingsDialog.get_speed_value(dialog)
            assert approx_equal(speed, 2.0), f"Speed should persist as 2x after Apply, got {speed}x"

            # Step 4: Set Speed to 1x (center), Apply
            VoiceSettingsDialog.set_speed_by_position(dialog, page, "center")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify 1x persisted, then set Volume to Mute
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            speed = VoiceSettingsDialog.get_speed_value(dialog)
            assert approx_equal(speed, 1.0), f"Speed should persist as 1x after Apply, got {speed}x"

            # Step 5: Set Volume to Mute (0%), Apply
            VoiceSettingsDialog.set_volume_by_position(dialog, page, "mute")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify 0% persisted, then set to 50%
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert volume == 0, f"Volume should persist as 0% after Apply, got {volume}%"

            # Step 6: Set Volume to 50%, Apply
            VoiceSettingsDialog.set_volume_by_position(dialog, page, "half")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify ~50% persisted, then set to 100%
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert 45 <= volume <= 55, f"Volume should persist as ~50% after Apply, got {volume}%"

            # Step 7: Set Volume to 100%, Apply
            VoiceSettingsDialog.set_volume_by_position(dialog, page, "full")
            VoiceSettingsDialog.click_apply(dialog)
            VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # Reopen - verify 100% persisted
            page.wait_for_timeout(1000)
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
            volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert volume == 100, f"Volume should persist as 100% after Apply, got {volume}%"
            VoiceSettingsDialog.click_cancel(dialog)

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as e:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, e)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1314_voice-settings-sync-between-chat-dialog-and-personalization-page.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_voice_settings_sync(self, page, conversation_api):
        """TC3: Settings Synchronization from Personalization to Chat.
        TC-1916
        Personalization settings are baseline defaults that apply to Chat.
        Chat changes are temporary/session-only and do NOT sync back to Personalization.

        Steps:
            1. Navigate to Personalization, note original Voice, Speed, Volume
            2. Change Voice, Speed (1.5x), Volume (75%) in Personalization
            3. Go to Chat, trigger TTS, open Voice Settings
            4. Verify all three settings match Personalization
        """
        conv_id = None
        original_voice = None
        original_speed = None
        original_volume = None
        try:
            # Step 1: Note original settings in Personalization
            settings = UserProfileSettingsPage(page)
            settings.navigate_to_personalization()
            original_voice = settings.get_current_voice()
            original_speed = settings.get_speed_value()
            original_volume = settings.get_volume_value()

            # Step 2: Change Voice, Speed, Volume in Personalization
            voices = settings.get_available_voices()
            new_voice = next((v for v in voices if v != original_voice), voices[0])
            new_speed = 1.5
            new_volume = 75

            settings.select_voice(new_voice)
            settings.set_speed(new_speed)
            settings.set_volume(new_volume)

            # Step 3: Go to Chat, trigger TTS
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)
            conv_id = capture_conversation_id(page)

            chat.send_message("Describe a sunset briefly.", use_enter=True)
            chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            if not conv_id:
                conv_id = capture_conversation_id(page)

            # Step 4: Verify all settings in Chat match Personalization
            dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)

            chat_voice = VoiceSettingsDialog.get_current_voice(dialog)
            assert chat_voice == new_voice, (
                f"Voice in Chat should be '{new_voice}' (from Personalization), got '{chat_voice}'"
            )

            chat_speed = VoiceSettingsDialog.get_speed_value(dialog)
            assert approx_equal(chat_speed, new_speed), (
                f"Speed in Chat should be {new_speed}x (from Personalization), got {chat_speed}x"
            )

            chat_volume = VoiceSettingsDialog.get_volume_value(dialog)
            assert 70 <= chat_volume <= 80, (
                f"Volume in Chat should be ~{new_volume}% (from Personalization), got {chat_volume}%"
            )

            VoiceSettingsDialog.click_cancel(dialog)

        finally:
            # Restore original settings
            if original_voice is not None:
                try:
                    settings = UserProfileSettingsPage(page)
                    settings.navigate_to_personalization()
                    if original_voice:
                        settings.select_voice(original_voice)
                    if original_speed is not None:
                        settings.set_speed(original_speed)
                    if original_volume is not None:
                        settings.set_volume(original_volume)
                except Exception as e:
                    logger.warning("Failed to restore settings: %s", e)
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as e:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, e)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1316_voice-personalization-page-all-controls-present-including-functional-p.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_voice_preview_personalization(self, page):
        """TC4: Voice Personalization Controls in Settings Page.
        TC-1914
        Steps:
            1. Navigate to User Settings > Personalization
            2. Verify Voice Personalization section visible
            3. Verify all controls present (Voice, Speed, Volume, Preview Voice)
            4. Change Voice, Speed, Volume - verify new values reflected
            5. Click Preview Voice button - verify it's clickable
        """
        original_voice = None
        original_speed = None
        original_volume = None
        try:
            # Step 1: Navigate to Personalization
            settings = UserProfileSettingsPage(page)
            settings.navigate_to_personalization()

            # Step 2: Verify Voice Personalization section visible
            assert settings.is_voice_personalization_visible(), (
                "Voice Personalization section should be visible"
            )

            # Step 3: Verify all controls present
            original_voice = settings.get_current_voice()
            assert original_voice, "Voice dropdown should show selected voice"

            original_speed = settings.get_speed_value()
            assert 0.5 <= original_speed <= 2.0, f"Speed should be 0.5x-2x, got {original_speed}x"

            original_volume = settings.get_volume_value()
            assert 0 <= original_volume <= 100, f"Volume should be 0-100%, got {original_volume}%"

            assert settings.is_preview_voice_button_visible(), "Preview Voice button should be visible"

            # Step 4: Change Voice, Speed, Volume - verify new values
            voices = settings.get_available_voices()
            assert len(voices) > 0, "Voice dropdown should have options"

            new_voice = next((v for v in voices if v != original_voice), voices[0])
            settings.select_voice(new_voice)
            assert settings.get_current_voice() == new_voice, f"Voice should change to {new_voice}"

            settings.set_speed(1.5)
            speed = settings.get_speed_value()
            assert approx_equal(speed, 1.5), f"Speed should be 1.5x, got {speed}x"

            settings.set_volume(75)
            volume = settings.get_volume_value()
            assert 70 <= volume <= 80, f"Volume should be ~75%, got {volume}%"

            # Step 5: Click Preview Voice - verify button is clickable
            settings.click_preview_voice()
            page.wait_for_timeout(1000)

        finally:
            # Restore original settings
            if original_voice or original_speed or original_volume:
                try:
                    settings = UserProfileSettingsPage(page)
                    settings.navigate_to_personalization()
                    if original_voice:
                        settings.select_voice(original_voice)
                    if original_speed:
                        settings.set_speed(original_speed)
                    if original_volume:
                        settings.set_volume(original_volume)
                except Exception as e:
                    logger.warning("Failed to restore settings: %s", e)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1341_voice-mini-player-not-visible-by-default-regression.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_voice_settings_not_visible_by_default(self, page, conversation_api):
        """TC5: Voice settings are NOT displayed in Chat by default.

        Regression test for bug #5235: Read-out control was inappropriately
        visible in default Chat window state.

        Steps:
            1. Navigate to Chat, create new conversation
            2. Send "hi" message and wait for AI response
            3. Verify Voice Mini Player is NOT visible after response by default

        Expected:
            Voice settings controls should only appear when Read-out and
            Voice mode features are explicitly activated.

        Related:
            - Bug: https://github.com/EliteaAI/elitea_issues/issues/5235
        """
        conv_id = None
        try:
            chat = ChatPage(page)
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)

            # Send message and wait for AI response
            chat.send_message("hi", use_enter=True)
            chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

            conv_id = capture_conversation_id(page)

            # Verify Voice Mini Player is NOT visible after AI response
            assert not chat.is_voice_mini_player_visible(), (
                "Voice Mini Player should NOT be visible in Chat by default. "
                "Voice features must be explicitly activated by user."
            )

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as e:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, e)
