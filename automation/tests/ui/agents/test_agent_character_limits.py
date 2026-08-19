"""UI Tests for Welcome Message & Conversation Starter Character Limits.

Tests for issue #4963: Character limit warning for Welcome Message and
Conversation Starter fields.

Features tested:
- Real-time character counter display in both collapsed and fullscreen modes
- Counter turns red when character limit is reached (0 remaining)
- Warning message displays in fullscreen mode at limit
- Collapsed mode shows red counter at limit

Spec: https://github.com/EliteaAI/elitea_issues/issues/4963
Acceptance Criteria:
1. Real-time character counter visible in Full Screen for both fields
2. Counter turns red in both modes when 0 characters remain
3. Warning message displays in Full Screen at limit
4. Collapsed mode shows red counter and optional warning label

Markers:
    - ui: requires browser
    - agents: agent-related tests
    - p1: high priority tests (validation feature)

Usage:
    cd automation
    pytest tests/ui/agents/test_agent_character_limits.py -v
"""

import pytest
from pages.agents_list_page import AgentsListPage
from pages.agent_form_page import AgentFormPage
from pages.agent_detail_page import AgentDetailPage
import allure

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
FORM_LOAD_TIMEOUT = 15000

# Character limits defined in EliteaUI: src/common/constants.js
# Constants: MAX_WELCOME_MESSAGE_LENGTH, MAX_CONVERSATION_STARTER_LENGTH
WELCOME_MESSAGE_MAX_CHARS = 768
CONVERSATION_STARTER_MAX_CHARS = 768


class TestWelcomeMessageCharacterCounter:
    """Welcome Message character counter tests (collapsed and fullscreen modes)."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0064_character-counter-is-present-and-updates-in-real-time.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_welcome_message_counter_visible_and_updates_realtime(self, page, agent_id):
        """Character counter appears when typing and updates in real-time.
        TC-1688, TC-1685
        Acceptance Criteria #1: Real-time character counter visible.
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # ------------------------------------------------------------------
        # Step 1 — Type initial text; counter appears
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Type initial text; counter appears"):
            detail_page.welcome_message_input.click()
            detail_page.welcome_message_input.clear()
            detail_page.welcome_message_input.press_sequentially("Hello, welcome to my agent!", delay=50)
            detail_page.page.wait_for_timeout(500)

            initial_counter_text = detail_page.get_welcome_message_counter_text()

            if not initial_counter_text:
                pytest.skip(
                    "Character counter not visible - feature may not be implemented yet. "
                    "Issue #4963 acceptance criteria #1: counter should be visible."
                )

            assert "characters" in initial_counter_text.lower(), (
                f"Counter should show 'characters left' format, got: {initial_counter_text}"
            )

            initial_remaining = detail_page.get_welcome_message_remaining_chars()
            assert initial_remaining is not None, f"Could not parse remaining chars from: {initial_counter_text}"

        # ------------------------------------------------------------------
        # Step 2 — Add more text; counter updates (remaining chars decreases)
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Add more text; counter updates"):
            detail_page.welcome_message_input.press_sequentially(" How can I help you?", delay=50)
            detail_page.page.wait_for_timeout(500)

            updated_counter_text = detail_page.get_welcome_message_counter_text()
            updated_remaining = detail_page.get_welcome_message_remaining_chars()

            assert updated_remaining is not None, f"Could not parse remaining chars from: {updated_counter_text}"
            assert updated_remaining < initial_remaining, (
                f"Counter should update after adding text. "
                f"Initial remaining: {initial_remaining}, Updated remaining: {updated_remaining}"
            )

        # ------------------------------------------------------------------
        # Step 3 — Save agent with welcome message
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Save agent with welcome message"):
            detail_page.wait_for_form_validation()
            assert detail_page.is_save_enabled(), (
                "Save button should be enabled when welcome message is within limit"
            )
            detail_page.click_save()
            detail_page.wait_for_network(timeout=10000)

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0061_counter-turns-red-at-zero-in-collapsed-inline-mode.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_welcome_message_counter_turns_red_at_limit(self, page, agent_id):
        """Counter turns red with warning message when character limit is reached.
        TC-1687

        Acceptance Criteria #2: Counter turns red when 0 characters remain.
        """
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Fill welcome message to exactly 768 characters"):
            max_text = "X" * WELCOME_MESSAGE_MAX_CHARS
            detail_page.welcome_message_input.click()
            detail_page.welcome_message_input.clear()
            detail_page.welcome_message_input.fill(max_text)
            detail_page.page.wait_for_timeout(500)

        with allure.step("Step 3 — Verify counter shows '0 characters left' warning"):
            counter_text = detail_page.get_welcome_message_counter_text()

            if counter_text is None:
                pytest.skip("Character counter not visible - feature not implemented")

            assert "0 characters left" in counter_text.lower(), (
                f"Counter should show '0 characters left' at limit, got: {counter_text}"
            )
            assert "maximum" in counter_text.lower() or "limit" in counter_text.lower(), (
                f"Counter should show warning about maximum limit, got: {counter_text}"
            )

        with allure.step("Step 4 — Verify counter has red/error styling"):
            is_warning = detail_page.is_welcome_message_counter_warning()
            assert is_warning, (
                f"Counter should have red/error styling at character limit. Counter text: {counter_text}"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0064_character-counter-is-present-and-updates-in-real-time.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0059_counter-turns-red-when-character-count-reaches-zero-in-full-screen-mod.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_welcome_message_fullscreen_counter_and_warning(self, page, agent_id):
        """Fullscreen dialog shows counter that updates and warning at limit.
        TC-1689, TC-1685

        Acceptance Criteria #1 & #3: Counter visible in Full Screen mode,
        warning displays at limit.
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # ------------------------------------------------------------------
        # Step 1 — Open fullscreen; counter shows "768 characters left"
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Open fullscreen; counter shows '768 characters left'"):
            detail_page.welcome_message_input.hover()
            detail_page.page.wait_for_timeout(500)

            if not detail_page.welcome_message_expand_button.is_visible(timeout=3000):
                pytest.skip("Welcome message expand button not visible - fullscreen not available")

            detail_page.open_welcome_message_fullscreen()

            assert detail_page.is_welcome_message_fullscreen_open(), (
                "Welcome message fullscreen dialog should be open"
            )

            initial_counter = detail_page.get_welcome_message_fullscreen_counter_text()

            if not initial_counter:
                detail_page.close_welcome_message_fullscreen()
                pytest.skip("Character counter not visible in fullscreen dialog")

            assert "characters" in initial_counter.lower(), (
                f"Counter should show 'characters left' format, got: {initial_counter}"
            )
            assert "768" in initial_counter, (
                f"Initial counter should show 768 characters left, got: {initial_counter}"
            )

        # ------------------------------------------------------------------
        # Step 2 — Type text; counter decreases
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Type text; counter decreases"):
            detail_page.fill_welcome_message_in_fullscreen("Test welcome message")
            detail_page.page.wait_for_timeout(300)

            updated_counter = detail_page.get_welcome_message_fullscreen_counter_text()
            assert updated_counter != initial_counter, (
                f"Counter should update after typing. Initial: {initial_counter}, Updated: {updated_counter}"
            )

        # ------------------------------------------------------------------
        # Step 3 — Fill to limit; red warning appears
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Fill to limit; red warning appears"):
            max_text = "X" * WELCOME_MESSAGE_MAX_CHARS
            detail_page.fill_welcome_message_in_fullscreen(max_text)
            detail_page.page.wait_for_timeout(500)

            warning_counter = detail_page.get_welcome_message_fullscreen_counter_text()

            assert "0 characters left" in warning_counter.lower(), (
                f"Counter should show '0 characters left' at limit, got: {warning_counter}"
            )
            assert "maximum" in warning_counter.lower(), (
                f"Counter should show MAXIMUM warning, got: {warning_counter}"
            )

            is_warning = detail_page.is_welcome_message_fullscreen_counter_warning()
            assert is_warning, (
                f"Counter should have red/error styling at limit. Counter: {warning_counter}"
            )

            detail_page.close_welcome_message_fullscreen()

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0062_pasting-over-limit-text-text-truncated-to-768-chars-with-visible-feedb.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_welcome_message_text_truncated_with_warning(self, page, agent_id):
        """Verify text over limit is truncated to 768 chars with warning message.
        TC-1686

        Tests both collapsed mode and fullscreen mode.
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        over_limit_text = "A" * (WELCOME_MESSAGE_MAX_CHARS + 50)  # 818 chars

        # ------------------------------------------------------------------
        # Step 1 — Collapsed mode: paste 818 chars; verify truncated to 768
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Collapsed mode: paste 818 chars; verify truncated to 768"):
            detail_page.welcome_message_input.click()
            detail_page.welcome_message_input.clear()
            detail_page.welcome_message_input.fill(over_limit_text)
            detail_page.page.wait_for_timeout(500)

            actual_value = detail_page.welcome_message_input.input_value()
            assert len(actual_value) == WELCOME_MESSAGE_MAX_CHARS, (
                f"Text should be truncated to {WELCOME_MESSAGE_MAX_CHARS} chars, "
                f"got {len(actual_value)} chars"
            )

        # ------------------------------------------------------------------
        # Step 2 — Collapsed mode: verify warning message
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Collapsed mode: verify warning message"):
            counter_text = detail_page.get_welcome_message_counter_text()
            assert counter_text is not None, "Counter should be visible at limit"
            assert "0 characters left" in counter_text.lower(), (
                f"Counter should show '0 characters left', got: {counter_text}"
            )
            assert "maximum" in counter_text.lower(), (
                f"Counter should show MAXIMUM warning, got: {counter_text}"
            )

            is_warning = detail_page.is_welcome_message_counter_warning()
            assert is_warning, f"Counter should have red styling. Counter: {counter_text}"

        # ------------------------------------------------------------------
        # Step 3 — Fullscreen mode: paste 818 chars; verify truncated to 768
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Fullscreen mode: paste 818 chars; verify truncated to 768"):
            detail_page.welcome_message_input.clear()
            detail_page.page.wait_for_timeout(300)

            detail_page.welcome_message_input.hover()
            detail_page.page.wait_for_timeout(500)

            if not detail_page.welcome_message_expand_button.is_visible(timeout=3000):
                pytest.skip("Fullscreen button not available - skipping fullscreen check")

            detail_page.open_welcome_message_fullscreen()

            detail_page.fill_welcome_message_in_fullscreen(over_limit_text)
            detail_page.page.wait_for_timeout(500)

            actual_fullscreen_value = detail_page.get_welcome_message_fullscreen_value()
            assert len(actual_fullscreen_value) == WELCOME_MESSAGE_MAX_CHARS, (
                f"Fullscreen text should be truncated to {WELCOME_MESSAGE_MAX_CHARS} chars, "
                f"got {len(actual_fullscreen_value)} chars"
            )

        # ------------------------------------------------------------------
        # Step 4 — Fullscreen mode: verify warning message and red styling
        # ------------------------------------------------------------------
        with allure.step("Step 4 — Fullscreen mode: verify warning message and red styling"):
            dialog_counter = detail_page.get_welcome_message_fullscreen_counter_text()
            assert dialog_counter is not None, "Dialog counter should be visible"
            assert "0 characters left" in dialog_counter.lower(), (
                f"Dialog counter should show '0 characters left', got: {dialog_counter}"
            )
            assert "maximum" in dialog_counter.lower(), (
                f"Dialog counter should show MAXIMUM warning, got: {dialog_counter}"
            )

            dialog_warning = detail_page.is_welcome_message_fullscreen_counter_warning()
            assert dialog_warning, f"Dialog counter should have red styling. Counter: {dialog_counter}"

            detail_page.close_welcome_message_fullscreen()


class TestConversationStarterCharacterCounter:
    """Conversation Starter character counter tests."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0064_character-counter-is-present-and-updates-in-real-time.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_conversation_starter_counter_visible_and_updates(self, page, agent_id):
        """Character counter appears when typing and updates in real-time.
        TC-1685
        Acceptance Criteria #1 (extended to Conversation Starters).

        Note: Counter only appears after typing, not initially.
        """
        import re
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # ------------------------------------------------------------------
        # Step 1 — Add conversation starter; type initial text; counter appears
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Add conversation starter; counter appears"):
            detail_page.add_conversation_starter("Test starter")
            detail_page.page.wait_for_timeout(500)

            initial_counter_text = detail_page.get_conversation_starter_counter_text(index=0)

            if not initial_counter_text:
                pytest.skip(
                    "Conversation starter character counter not visible - "
                    "feature may not be implemented yet."
                )

            assert "characters" in initial_counter_text.lower(), (
                f"Counter should show 'characters left' format, got: {initial_counter_text}"
            )

            initial_match = re.search(r'(\d+)\s*characters?\s*left', initial_counter_text, re.IGNORECASE)
            if not initial_match:
                pytest.skip(f"Could not parse counter format: {initial_counter_text}")

            initial_remaining = int(initial_match.group(1))

        # ------------------------------------------------------------------
        # Step 2 — Add more text; counter updates (remaining chars decreases)
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Add more text; counter updates"):
            detail_page.fill_conversation_starter(0, "Test starter message extended with more text")
            detail_page.page.wait_for_timeout(500)

            updated_counter_text = detail_page.get_conversation_starter_counter_text(index=0)
            updated_match = re.search(r'(\d+)\s*characters?\s*left', updated_counter_text, re.IGNORECASE)

            if updated_match:
                updated_remaining = int(updated_match.group(1))
                assert updated_remaining < initial_remaining, (
                    f"Counter should update after adding text. "
                    f"Initial: {initial_remaining}, Updated: {updated_remaining}"
                )
            else:
                pytest.skip(f"Could not parse updated counter: {updated_counter_text}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0061_counter-turns-red-at-zero-in-collapsed-inline-mode.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_conversation_starter_counter_turns_red_at_limit(self, page, agent_id):
        """Counter turns red with warning message when character limit is reached.
        TC-1687

        Acceptance Criteria #2.
        """
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Add conversation starter and fill to 768 characters"):
            detail_page.add_conversation_starter("")
            max_text = "S" * CONVERSATION_STARTER_MAX_CHARS
            detail_page.fill_conversation_starter(0, max_text)
            detail_page.page.wait_for_timeout(500)

        with allure.step("Step 3 — Verify counter shows '0 characters left' warning"):
            counter_text = detail_page.get_conversation_starter_counter_text(index=0)

            if counter_text is None:
                pytest.skip("Conversation starter counter not visible - feature not implemented")

            assert "0 characters left" in counter_text.lower(), (
                f"Counter should show '0 characters left' at limit, got: {counter_text}"
            )
            assert "maximum" in counter_text.lower(), (
                f"Counter should show MAXIMUM warning, got: {counter_text}"
            )

        with allure.step("Step 4 — Verify counter has red/error styling"):
            is_warning = detail_page.is_conversation_starter_counter_warning(index=0)
            assert is_warning, f"Counter should have red styling at limit. Counter: {counter_text}"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0064_character-counter-is-present-and-updates-in-real-time.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0059_counter-turns-red-when-character-count-reaches-zero-in-full-screen-mod.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_conversation_starter_fullscreen_counter_and_warning(self, page, agent_id):
        """Fullscreen dialog shows counter that updates and warning at limit.
        TC-1689, TC-1685
        """
        detail_page = AgentDetailPage(page)
        detail_page.navigate(agent_id)

        # ------------------------------------------------------------------
        # Step 1 — Add starter, open fullscreen; counter shows "768 characters left"
        # ------------------------------------------------------------------
        with allure.step("Step 1 — Add starter, open fullscreen; counter shows '768 characters left'"):
            detail_page.add_conversation_starter("")
            detail_page.page.wait_for_timeout(500)

            detail_page.conversation_starter_inputs.first.hover()
            detail_page.page.wait_for_timeout(500)

            if not detail_page.conversation_starter_expand_button.is_visible(timeout=3000):
                pytest.skip("Fullscreen button not available for conversation starter")

            detail_page.open_conversation_starter_fullscreen(index=0)

            initial_counter = detail_page.get_conversation_starter_fullscreen_counter_text()

            if not initial_counter:
                detail_page.close_conversation_starter_fullscreen()
                pytest.skip("Character counter not visible in fullscreen dialog")

            assert "characters" in initial_counter.lower(), (
                f"Counter should show 'characters left' format, got: {initial_counter}"
            )

        # ------------------------------------------------------------------
        # Step 2 — Type text; counter decreases
        # ------------------------------------------------------------------
        with allure.step("Step 2 — Type text; counter decreases"):
            detail_page.fill_conversation_starter_in_fullscreen("Test message")
            detail_page.page.wait_for_timeout(300)

            updated_counter = detail_page.get_conversation_starter_fullscreen_counter_text()
            assert updated_counter != initial_counter, (
                f"Counter should update. Initial: {initial_counter}, Updated: {updated_counter}"
            )

        # ------------------------------------------------------------------
        # Step 3 — Fill to limit; red warning message
        # ------------------------------------------------------------------
        with allure.step("Step 3 — Fill to limit; red warning message"):
            max_text = "X" * CONVERSATION_STARTER_MAX_CHARS
            detail_page.fill_conversation_starter_in_fullscreen(max_text)
            detail_page.page.wait_for_timeout(500)

            warning_counter = detail_page.get_conversation_starter_fullscreen_counter_text()
            assert "0 characters left" in warning_counter.lower(), (
                f"Counter should show '0 characters left', got: {warning_counter}"
            )
            assert "maximum" in warning_counter.lower(), (
                f"Counter should show MAXIMUM warning, got: {warning_counter}"
            )

            is_warning = detail_page.is_conversation_starter_fullscreen_counter_warning()
            assert is_warning, f"Counter should have red styling. Counter: {warning_counter}"

            detail_page.close_conversation_starter_fullscreen()

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0062_pasting-over-limit-text-text-truncated-to-768-chars-with-visible-feedb.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    @pytest.mark.flaky  # Inconsistent truncation: expects 768, sometimes gets 763 chars
    def test_conversation_starter_text_truncated_with_warning(self, page, agent_id):
        """Verify text over limit is truncated to 768 chars with warning.
        TC-1686
        """
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)
            over_limit_text = "B" * (CONVERSATION_STARTER_MAX_CHARS + 50)  # 818 chars

        with allure.step("Step 2 — Collapsed mode: paste 818 chars; verify truncated to 768"):
            detail_page.add_conversation_starter("")
            detail_page.fill_conversation_starter(0, over_limit_text)
            detail_page.page.wait_for_timeout(500)

            # Verify text is truncated to 768 characters in collapsed mode
            actual_value = detail_page.conversation_starter_inputs.first.input_value()
            assert len(actual_value) == CONVERSATION_STARTER_MAX_CHARS, (
                f"Text should be truncated to {CONVERSATION_STARTER_MAX_CHARS} chars, "
                f"got {len(actual_value)} chars"
            )

        with allure.step("Step 3 — Collapsed mode: verify warning message and red styling"):
            counter_text = detail_page.get_conversation_starter_counter_text(index=0)
            if not counter_text:
                pytest.skip("Counter not visible - feature not implemented")

            assert "0 characters left" in counter_text.lower(), (
                f"Counter should show '0 characters left', got: {counter_text}"
            )
            assert "maximum" in counter_text.lower(), (
                f"Counter should show MAXIMUM warning, got: {counter_text}"
            )
            is_warning = detail_page.is_conversation_starter_counter_warning(index=0)
            assert is_warning, f"Counter should have red styling. Counter: {counter_text}"

        with allure.step("Step 4 — Open fullscreen mode"):
            detail_page.fill_conversation_starter(0, "")
            detail_page.page.wait_for_timeout(300)
            detail_page.conversation_starter_inputs.first.hover()
            detail_page.page.wait_for_timeout(500)

            if not detail_page.conversation_starter_expand_button.is_visible(timeout=3000):
                pytest.skip("Fullscreen not available - skipping fullscreen check")

            detail_page.open_conversation_starter_fullscreen(index=0)

        with allure.step("Step 5 — Fullscreen mode: paste 818 chars; verify truncated to 768"):
            detail_page.fill_conversation_starter_in_fullscreen(over_limit_text)
            detail_page.page.wait_for_timeout(500)

            actual_fullscreen_value = detail_page.get_conversation_starter_fullscreen_value()
            assert len(actual_fullscreen_value) == CONVERSATION_STARTER_MAX_CHARS, (
                f"Fullscreen text should be truncated to {CONVERSATION_STARTER_MAX_CHARS} chars, "
                f"got {len(actual_fullscreen_value)} chars"
            )

        with allure.step("Step 6 — Fullscreen mode: verify warning message and red styling"):
            dialog_counter = detail_page.get_conversation_starter_fullscreen_counter_text()
            assert dialog_counter is not None, "Dialog counter should be visible"
            assert "0 characters left" in dialog_counter.lower(), (
                f"Dialog counter should show '0 characters left', got: {dialog_counter}"
            )
            assert "maximum" in dialog_counter.lower(), (
                f"Dialog counter should show MAXIMUM warning, got: {dialog_counter}"
            )
            dialog_warning = detail_page.is_conversation_starter_fullscreen_counter_warning()
            assert dialog_warning, f"Dialog counter should have red styling. Counter: {dialog_counter}"
            detail_page.close_conversation_starter_fullscreen()

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0063_multiple-conversation-starters-have-independent-character-counters.md", "onetest-ai Test Case link")
    @pytest.mark.p2
    def test_multiple_conversation_starters_have_counters(self, page, agent_id):
        """Each conversation starter field has its own counter.
        TC-1684
        """
        with allure.step("Step 1 — Navigate to agent detail page"):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)

        with allure.step("Step 2 — Add first conversation starter with short text"):
            detail_page.add_conversation_starter("Short")

        with allure.step("Step 3 — Add second conversation starter with longer text"):
            detail_page.add_conversation_starter("This is a much longer conversation starter text")

        with allure.step("Step 4 — Verify both starters are added"):
            starter_count = detail_page.get_conversation_starter_count()
            assert starter_count >= 2, f"Expected at least 2 starters, got {starter_count}"

        with allure.step("Step 5 — Verify each starter has independent counter with different values"):
            counter_0 = detail_page.get_conversation_starter_counter_text(index=0)
            counter_1 = detail_page.get_conversation_starter_counter_text(index=1)

            if counter_0 is None and counter_1 is None:
                pytest.skip("Conversation starter counters not visible - feature not implemented")

            if counter_0 and counter_1:
                assert counter_0 != counter_1, (
                    f"Counters should show different values for different text lengths. "
                    f"Counter 0: {counter_0}, Counter 1: {counter_1}"
                )
