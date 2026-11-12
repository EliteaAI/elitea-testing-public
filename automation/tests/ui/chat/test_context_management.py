"""UI Tests for Default Context Management Settings.

Verifies that the Context window mode (Balanced / Full) configured in the
personal Settings -> Memory page propagates to a brand-new chat — the
Context management widget shows the matching mode and window size
(EliteaAI/elitea_issues#6898 replaced the old Max Context Tokens field).

Test class:
    TestContextManagementSettings

Markers:
    - ui:  requires browser
    - p1:  high priority (primary flow)
    - p2:  medium priority (variation)

Usage:
    cd automation
    pytest tests/ui/chat/test_context_management.py -v
    pytest tests/ui/chat/test_context_management.py -v -m p1
"""

import re
import logging

import pytest
from pages.chat_page import ChatPage
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import expect
import allure

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
AI_RESPONSE_TIMEOUT = 30_000   # AI message generation (streaming)
UI_ELEMENT_TIMEOUT = 10_000    # Buttons, panels, dropdowns
NAVIGATION_TIMEOUT = 15_000    # SPA route changes
AUTOSAVE_TIMEOUT = 5_000       # Profile setting autosave round-trip


BALANCED_CAP_TOKENS = 272_000  # Balanced window cap (contextStrategy.constants.js BALANCED_WINDOW_TOKENS)


def _window_label(tokens: int) -> str:
    """Format a window size the way the widget does (formatWindowSize: 272000 -> '272K', 1048576 -> '1M')."""
    if tokens >= 1_000_000:
        return f"{round(tokens / 1_000_000, 1):g}M"
    return f"{round(tokens / 1000)}K"


class TestContextManagementSettings:
    """Verify that the personal Context window mode propagates to new chats.

    Flow under test:
        1. User opens Settings -> Memory and picks a Context window mode.
        2. The choice autosaves and survives a page reload.
        3. User starts a new chat and sends a message.
        4. The Context management widget shows the same mode, and the mode's
           window size matches the selected model's window from the model catalog.

    Cleanup:
        The user's original mode is restored and the created conversation is
        deleted via the API in the finally block.
    """

    @pytest.mark.parametrize("expected_mode", [
        pytest.param("full", marks=pytest.mark.p1, id="full_mode"),
        pytest.param("balanced", marks=pytest.mark.p2, id="balanced_mode"),
    ])
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-3744_context-budget-panel-reflects-profile-max-tokens.md", "onetest-ai Test Case link")
    @pytest.mark.tms("ELITEA-3744")
    def test_context_budget_reflects_profile_max_tokens(self, page, conversation_api, credential_api, expected_mode):
        """New chat's Context management widget reflects the personal Context window mode.

        Parameterized to verify:
        - P1 (Full): window = the model's full context window
        - P2 (Balanced): window = min(272,000, model window); updated value is not cached

        Cleanup: restores the original mode, deletes the created conversation via API.
        """
        conv_id = None

        profile = UserProfileSettingsPage(page)
        profile.navigate_to_profile()
        original_mode = profile.get_context_window_mode()

        try:
            # ------------------------------------------------------------------
            # Step 1-2 — Settings -> Memory: select the mode, reload, verify persisted
            # ------------------------------------------------------------------
            with allure.step(f"Step 1-2 — Set Context window to {expected_mode} and verify it persists after reload"):
                expect(profile.context_window_mode_group).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                profile.select_context_window_mode(expected_mode)

                page.reload()
                profile.wait_for_page_load()

                assert profile.get_context_window_mode() == expected_mode, (
                    f"Context window should still be '{expected_mode}' after reload"
                )

            # ------------------------------------------------------------------
            # Step 3 — Navigate to chat and create a new conversation
            # ------------------------------------------------------------------
            with allure.step("Step 3 — Navigate to chat and create a new conversation"):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

                match = re.search(r"/chat/(\d+)", page.url)
                if match:
                    conv_id = match.group(1)
                    logger.info("Conversation created with ID: %s", conv_id)

            # ------------------------------------------------------------------
            # Step 4 — Send a short message; wait for the AI answer
            # ------------------------------------------------------------------
            with allure.step("Step 4 — Send a short message and wait for the AI response"):
                chat.send_message(f"at_ctx_window_test_{expected_mode}", use_enter=True)
                chat.wait_for_input_ready(timeout=NAVIGATION_TIMEOUT)

                if not conv_id:
                    page.wait_for_url(lambda url: re.search(r"/chat/\d+", url) is not None, timeout=NAVIGATION_TIMEOUT)
                    conv_id = re.search(r"/chat/(\d+)", page.url).group(1)
                    logger.info("Conversation ID found after first message: %s", conv_id)

                # The AI answer is done once its action icons render.
                expect(chat.copy_text_action_button.first).to_be_attached(timeout=AI_RESPONSE_TIMEOUT * 3)
                chat.wait_for_context_management_widget(timeout=UI_ELEMENT_TIMEOUT * 6)

            # ------------------------------------------------------------------
            # Step 5 — Widget shows the matching mode and the model's window
            # ------------------------------------------------------------------
            with allure.step(f"Step 5 — Verify widget shows {expected_mode} and the correct window size"):
                # Independent oracle: the model catalog, not the widget itself.
                model_name = (chat.model_selector_name.first.text_content() or "").strip()
                catalog = credential_api.list_models(include_shared=True)
                windows = {m.get("display_name"): m.get("context_window") for m in catalog.get("items", [])}
                assert model_name in windows, (
                    f"Selected model '{model_name}' not found in the model catalog {sorted(windows)}"
                )
                model_window = windows[model_name]
                assert model_window, f"Catalog has no context_window for '{model_name}'"

                expected_window = (
                    model_window if expected_mode == "full" else min(BALANCED_CAP_TOKENS, model_window)
                )

                state = chat.get_context_window_mode_state()
                assert state["selected"] == expected_mode, (
                    f"Widget should show window mode '{expected_mode}', got '{state['selected']}'"
                )

                tab_label = state["full_label"] if expected_mode == "full" else state["balanced_label"]
                expected_label = f"{expected_mode.capitalize()} · {_window_label(expected_window)}"
                assert tab_label == expected_label, (
                    f"Selected mode's window should read '{expected_label}' "
                    f"(model '{model_name}' window {model_window}), got '{tab_label}'"
                )

                # The usable budget ('of N tokens') is the window minus a small safety margin.
                available = chat.get_context_budget_available_tokens()
                assert 0.9 * expected_window <= available <= expected_window, (
                    f"Available tokens {available} should be within 10% below the {expected_mode} "
                    f"window {expected_window}"
                )

        finally:
            # Restore the user's original mode (a persistent personal setting).
            try:
                profile = UserProfileSettingsPage(page)
                profile.navigate_to_profile()
                profile.select_context_window_mode(original_mode)
                logger.info("Restored Context window mode to %s", original_mode)
            except Exception as exc:
                logger.warning("Failed to restore Context window mode: %s", exc)
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Cleaned up conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_id, exc)
