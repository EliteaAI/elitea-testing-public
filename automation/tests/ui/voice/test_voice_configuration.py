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
from playwright.sync_api import expect
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
    match = re.search(r"/chat/(\d+)", page.url)
    return match.group(1) if match else None


class TestVoiceConfiguration:
    """Voice Configuration Settings tests matching manual test cases."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1315_apply-saves-and-cancel-discards-voice-settings-changes.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/voice/voice-configuration-settings/ELITEA-1312_voice-settings-dialog-opens-and-displays-all-controls-including-voice.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_voice_selection_from_chat(self, page, conversation_api):
        """TC1: Voice Selection via TTS Controls in Chat.
        TC-1918, TC-1915
        """
        conv_id = None
        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to Chat, send a message, wait for AI response
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to Chat, send a message, wait for AI response"):
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

            # ------------------------------------------------------------------
            # Step 2-3 — Click 'Read out' icon; click gear/settings icon
            # ------------------------------------------------------------------
            with allure.step("Step 2-3 — Click 'Read out' icon; click gear/settings icon"):
                chat.click_read_out(message_index=-1, timeout=TTS_TIMEOUT)
                chat.wait_for_tts_controls(timeout=TTS_TIMEOUT)
                dialog = chat.open_voice_settings_from_tts(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 4 — Inspect all dialog elements (Voice, Speed, Volume, Cancel, Apply)
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Inspect all dialog elements"):
                assert VoiceSettingsDialog.is_open(page), "Voice Settings dialog should be open"

                current_voice = VoiceSettingsDialog.get_current_voice(dialog)
                assert current_voice, "Voice dropdown should show a selected voice"

                speed = VoiceSettingsDialog.get_speed_value(dialog)
                assert 0.5 <= speed <= 2.0, f"Speed should be between 0.5x-2x, got {speed}x"

                volume = VoiceSettingsDialog.get_volume_value(dialog)
                assert 0 <= volume <= 100, f"Volume should be between 0-100%, got {volume}%"

                assert VoiceSettingsDialog.is_cancel_button_visible(dialog), "Cancel button should be visible"
                assert VoiceSettingsDialog.is_apply_button_visible(dialog), "Apply button should be visible"

            # ------------------------------------------------------------------
            # Step 5 — Click Voice dropdown; verify non-empty list
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Click Voice dropdown; verify non-empty list"):
                voices = VoiceSettingsDialog.get_available_voices(dialog, page)
                assert len(voices) > 0, "Voice dropdown should have options"

            # ------------------------------------------------------------------
            # Step 6 — Select a voice different from current
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Select a voice different from current"):
                original_voice = VoiceSettingsDialog.get_current_voice(dialog)
                new_voice = next((v for v in voices if v != original_voice), voices[0])
                VoiceSettingsDialog.select_voice(dialog, page, new_voice)

                selected_voice = VoiceSettingsDialog.get_current_voice(dialog)
                assert selected_voice == new_voice, f"Selected voice should be {new_voice}"

            # ------------------------------------------------------------------
            # Step 7 — Click Apply; dialog closes, voice saved
            # ------------------------------------------------------------------
            with allure.step("Step 7 — Click Apply; dialog closes, voice saved"):
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 8 — Re-open Voice Settings; verify voice persisted
            # ------------------------------------------------------------------
            with allure.step("Step 8 — Re-open Voice Settings; verify voice persisted"):
                page.wait_for_timeout(1000)
                dialog = chat.open_voice_settings_from_tts(timeout=UI_ELEMENT_TIMEOUT)

                persisted_voice = VoiceSettingsDialog.get_current_voice(dialog)
                assert persisted_voice == new_voice, (
                    f"Voice should persist as '{new_voice}' after Apply, got '{persisted_voice}'"
                )

            # ------------------------------------------------------------------
            # Step 9 — Change voice again, click Cancel; verify reverts
            # ------------------------------------------------------------------
            with allure.step("Step 9 — Change voice again, click Cancel; verify reverts"):
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

            # ------------------------------------------------------------------
            # Step 1 — Open Voice Settings; verify defaults (Speed 1x, Volume 100%)
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Open Voice Settings; verify defaults"):
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                speed = VoiceSettingsDialog.get_speed_value(dialog)
                volume = VoiceSettingsDialog.get_volume_value(dialog)
                assert approx_equal(speed, 1.0), f"Default speed should be 1x, got {speed}x"
                assert volume == 100, f"Default volume should be 100%, got {volume}%"

            # ------------------------------------------------------------------
            # Step 2 — Set Speed to 0.5x, Apply, reopen; verify persisted
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Set Speed to 0.5x, Apply, reopen; verify persisted"):
                VoiceSettingsDialog.set_speed_by_position(dialog, page, "min")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_timeout(1000)
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                speed = VoiceSettingsDialog.get_speed_value(dialog)
                assert approx_equal(speed, 0.5), f"Speed should persist as 0.5x after Apply, got {speed}x"

            # ------------------------------------------------------------------
            # Step 3 — Set Speed to 2x, Apply, reopen; verify 2x persisted
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Set Speed to 2x, Apply, reopen; verify 2x persisted"):
                VoiceSettingsDialog.set_speed_by_position(dialog, page, "max")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_timeout(1000)
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                speed = VoiceSettingsDialog.get_speed_value(dialog)
                assert approx_equal(speed, 2.0), f"Speed should persist as 2x after Apply, got {speed}x"

            # ------------------------------------------------------------------
            # Step 4 — Set Speed to 1x, Apply, reopen; verify 1x persisted
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Set Speed to 1x, Apply, reopen; verify 1x persisted"):
                VoiceSettingsDialog.set_speed_by_position(dialog, page, "center")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_timeout(1000)
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                speed = VoiceSettingsDialog.get_speed_value(dialog)
                assert approx_equal(speed, 1.0), f"Speed should persist as 1x after Apply, got {speed}x"

            # ------------------------------------------------------------------
            # Step 5 — Set Volume to Mute (0%), Apply, reopen; verify 0% persisted
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Set Volume to Mute (0%), Apply, reopen; verify 0% persisted"):
                VoiceSettingsDialog.set_volume_by_position(dialog, page, "mute")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_timeout(1000)
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                volume = VoiceSettingsDialog.get_volume_value(dialog)
                assert volume == 0, f"Volume should persist as 0% after Apply, got {volume}%"

            # ------------------------------------------------------------------
            # Step 6 — Set Volume to 50%, Apply, reopen; verify ~50% persisted
            # ------------------------------------------------------------------
            with allure.step("Step 6 — Set Volume to 50%, Apply, reopen; verify ~50% persisted"):
                VoiceSettingsDialog.set_volume_by_position(dialog, page, "half")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

                page.wait_for_timeout(1000)
                dialog = chat.trigger_tts_and_open_settings(timeout=TTS_TIMEOUT)
                volume = VoiceSettingsDialog.get_volume_value(dialog)
                assert 45 <= volume <= 55, f"Volume should persist as ~50% after Apply, got {volume}%"

            # ------------------------------------------------------------------
            # Step 7 — Set Volume to 100%, Apply, reopen; verify 100% persisted
            # ------------------------------------------------------------------
            with allure.step("Step 7 — Set Volume to 100%, Apply, reopen; verify 100% persisted"):
                VoiceSettingsDialog.set_volume_by_position(dialog, page, "full")
                VoiceSettingsDialog.click_apply(dialog)
                VoiceSettingsDialog.wait_for_closed(page, timeout=UI_ELEMENT_TIMEOUT)

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
        """
        conv_id = None
        original_voice = None
        original_speed = None
        original_volume = None
        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to Personalization; note original Voice, Speed, Volume
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to Personalization; note original settings"):
                settings = UserProfileSettingsPage(page)
                settings.navigate_to_personalization()
                original_voice = settings.get_current_voice()
                original_speed = settings.get_speed_value()
                original_volume = settings.get_volume_value()

            # ------------------------------------------------------------------
            # Step 2 — Change Voice, Speed (1.5x), Volume (75%) in Personalization
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Change Voice, Speed (1.5x), Volume (75%) in Personalization"):
                voices = settings.get_available_voices()
                new_voice = next((v for v in voices if v != original_voice), voices[0])
                new_speed = 1.5
                new_volume = 75

                settings.select_voice(new_voice)
                settings.set_speed(new_speed)
                settings.set_volume(new_volume)

            # ------------------------------------------------------------------
            # Step 3 — Go to Chat, trigger TTS, open Voice Settings
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Go to Chat, trigger TTS, open Voice Settings"):
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

            # ------------------------------------------------------------------
            # Step 4 — Verify all three settings match Personalization
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Verify all three settings match Personalization"):
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
        """
        original_voice = None
        original_speed = None
        original_volume = None
        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to User Settings > Personalization
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to User Settings > Personalization"):
                settings = UserProfileSettingsPage(page)
                settings.navigate_to_personalization()

            # ------------------------------------------------------------------
            # Step 2 — Verify Voice Personalization section visible
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Verify Voice Personalization section visible"):
                assert settings.is_voice_personalization_visible(), (
                    "Voice Personalization section should be visible"
                )

            # ------------------------------------------------------------------
            # Step 3 — Verify all controls present (Voice, Speed, Volume, Preview Voice)
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Verify all controls present"):
                original_voice = settings.get_current_voice()
                assert original_voice, "Voice dropdown should show selected voice"

                original_speed = settings.get_speed_value()
                assert 0.5 <= original_speed <= 2.0, f"Speed should be 0.5x-2x, got {original_speed}x"

                original_volume = settings.get_volume_value()
                assert 0 <= original_volume <= 100, f"Volume should be 0-100%, got {original_volume}%"

                assert settings.is_preview_voice_button_visible(), "Preview Voice button should be visible"

            # ------------------------------------------------------------------
            # Step 4 — Change Voice, Speed, Volume; verify new values reflected
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Change Voice, Speed, Volume; verify new values reflected"):
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

            # ------------------------------------------------------------------
            # Step 5 — Click Preview Voice button; verify it's clickable
            # ------------------------------------------------------------------
            with allure.step("Step 5 — Click Preview Voice button; verify it's clickable"):
                settings.click_preview_voice()
                page.wait_for_timeout(1000)

        finally:
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

        Expected:
            Voice settings controls should only appear when Read-out and
            Voice mode features are explicitly activated.

        Related:
            - Bug: https://github.com/EliteaAI/elitea_issues/issues/5235
        """
        conv_id = None
        try:
            # ------------------------------------------------------------------
            # Step 1 — Navigate to Chat, create new conversation
            # ------------------------------------------------------------------
            with allure.step("Step 1 — Navigate to Chat, create new conversation"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 2 — Send "hi" message and wait for AI response
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Send 'hi' message and wait for AI response"):
                chat.send_message("hi", use_enter=True)
                chat.wait_for_ai_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

                conv_id = capture_conversation_id(page)

            # ------------------------------------------------------------------
            # Step 3 — Verify Voice Mini Player is NOT visible after response by default
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Verify Voice Mini Player is NOT visible by default"):
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

    @pytest.mark.p2
    @pytest.mark.regression
    def test_play_stop_toggle_and_disabled_controls(self, page, conversation_api):
        """GAP-018: Voice mini-player Play/Stop toggle + controls disabled
        during read-out playback.

        Coverage-gap campaign case (cov60) — no onetest TMS case and no
        numbered tracker issue exist for the case itself, only the local
        board ledger. Coverage target: VoiceControlButton.jsx's
        isPlaying-driven icon/disabled branches, ApplicationAnswer.jsx's
        `!!speakingMessageId` read-out disable branch (unconditional on ALL
        rendered read-out buttons, not just "other" answers), and
        useReadAloud's mini-player mount-on-read-out / unmount-on-stop
        behavior (it unmounts entirely rather than resetting in place).

        Tooltip TEXT ("Start speaking"/"Stop speaking") is intentionally not
        asserted — see ChatPage.is_play_stop_showing_stop_icon() docstring;
        the icon-path + settings-disabled-state checks together cover the
        full `isPlaying` state surface without a non-testid locator.

        Spec: test-specs/chat-interface/l3_voice-mini-player-play-stop-toggle-and-disabled-controls_GAP-018.md
        Source: .agents/automation-board/batches/cov60/cases/GAP-018/source.md
        """
        conv_id = None
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        try:
            with allure.step(
                "Step 1 — Send two prompts (short, then long) so 2 AI answers with "
                "speakable text render; both read-out buttons present and enabled"
            ):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_new_conversation(timeout=NAVIGATION_TIMEOUT)
                conv_id = capture_conversation_id(page)

                initial_count = chat.get_message_count()
                chat.send_message("Say hello in one sentence.", use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

                if not conv_id:
                    conv_id = capture_conversation_id(page)

                # Longer prompt for the answer that will actually be played — a
                # short answer's TTS can finish in well under 1s, racing past the
                # "Stop" state window before it's ever observed (AFS Test Data).
                initial_count = chat.get_message_count()
                chat.send_message(
                    "Write a 6 to 8 sentence paragraph describing a peaceful "
                    "morning by a lake.",
                    use_enter=True,
                )
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
                chat.wait_for_generation_complete(timeout=AI_RESPONSE_TIMEOUT)

                read_out_states = chat.get_read_out_buttons_disabled_states()
                assert len(read_out_states) == 2, (
                    f"Expected 2 read-out buttons (one per AI answer), got {len(read_out_states)}"
                )
                assert read_out_states == [False, False], (
                    f"Both read-out buttons should be enabled before any playback, got {read_out_states}"
                )

            with allure.step(
                "Step 2 — Click the most recent (longer) answer's read-out; "
                "mini-player appears in idle/Play state (playback not yet started)"
            ):
                chat.click_read_out(message_index=-1, timeout=TTS_TIMEOUT)
                chat.wait_for_tts_controls(timeout=TTS_TIMEOUT)

                expect(chat.voice_mini_player).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                chat.voice_play_stop_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                chat.voice_settings_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_play_stop_showing_stop_icon(timeout=UI_ELEMENT_TIMEOUT), (
                    "Clicking Read-out alone must only stage playback (Play/idle icon) — "
                    "audio starts only once the play/stop button itself is clicked"
                )

            with allure.step(
                "Step 3 — Click play/stop (currently Play) to start playback; "
                "it now renders the Stop icon"
            ):
                chat.click_play_stop_button(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_play_stop_showing_stop_icon(timeout=UI_ELEMENT_TIMEOUT), (
                    "Play/stop button should render the Stop icon while audio is playing"
                )

            with allure.step("Step 4 — While playing, chat-voice-settings-button is disabled"):
                assert chat.is_voice_settings_button_disabled(), (
                    "Voice settings button should be disabled while isPlaying is true"
                )

            with allure.step(
                "Step 5 — While playing, EVERY chat-read-out-button is disabled "
                "(not just the other answer's)"
            ):
                read_out_states = chat.get_read_out_buttons_disabled_states()
                assert read_out_states == [True, True], (
                    f"All read-out buttons should be disabled while a message is speaking, "
                    f"got {read_out_states} (the disable condition is unconditional on "
                    "!!speakingMessageId, including the currently-speaking answer's own button)"
                )

            with allure.step(
                "Step 6 — Click play/stop (currently Stop) to stop playback; "
                "the mini-player fully unmounts"
            ):
                chat.click_play_stop_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.voice_mini_player).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 7 — After stopping, every chat-read-out-button is enabled again"):
                read_out_states = chat.get_read_out_buttons_disabled_states()
                assert read_out_states == [False, False], (
                    f"All read-out buttons should be re-enabled once playback stops, got {read_out_states}"
                )
                # chat-voice-settings-button is not present to re-check — the
                # mini-player unmounted entirely in Step 6; expected, not a gap.

            with allure.step(
                "Step 8 — Round-trip the toggle a second time: mini-player reappears, "
                "Stop→Play round-trips cleanly again"
            ):
                chat.click_read_out(message_index=-1, timeout=TTS_TIMEOUT)
                chat.wait_for_tts_controls(timeout=TTS_TIMEOUT)
                expect(chat.voice_mini_player).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)

                chat.click_play_stop_button(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_play_stop_showing_stop_icon(timeout=UI_ELEMENT_TIMEOUT), (
                    "Second round-trip: play/stop button should show the Stop icon again "
                    "after re-starting playback"
                )

                chat.click_play_stop_button(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.voice_mini_player).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

                read_out_states = chat.get_read_out_buttons_disabled_states()
                assert read_out_states == [False, False], (
                    f"After the second stop, all read-out buttons should be enabled again, "
                    f"got {read_out_states}"
                )

            unexpected_errors = [m.text for m in console_errors]
            assert not unexpected_errors, (
                f"Expected zero console errors across the play/stop toggle flow, got: {unexpected_errors}"
            )

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                except Exception as e:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, e)
