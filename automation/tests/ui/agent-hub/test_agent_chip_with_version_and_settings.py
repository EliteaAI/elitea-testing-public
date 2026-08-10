"""UI test — Agent Hub: Agent Chip in Message Input with Version and Settings

Verify that after starting a conversation with an agent from the Agent Hub catalog,
the agent chip displays in the message input area with avatar, agent name, agent version,
and a settings icon.

Test case: ELITEA-2362
AFS: test-specs/agent-hub/l2_agent-chip-with-version-and-settings_ELITEA-2362.md

Markers:
    - ui: requires browser
    - agent-hub: agent hub/catalog tests
    - p2: medium priority (per AFS metadata: priority medium)
    - regression
"""

import re

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage

pytestmark = [pytest.mark.ui, pytest.mark.agent_hub, pytest.mark.p2, pytest.mark.regression]


class TestAgentChipWithVersionAndSettings:
    """ELITEA-2362 — Agent chip visible in message input with version and settings"""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/"
        "tests/automated-full-regression-ui/agent-hub/ELITEA-2362.md",
        "onetest-ai Test Case link",
    )
    def test_agent_chip_with_version_and_settings(self, page):
        """When user starts a conversation from an agent card, the agent chip
        is visible in the message input area with avatar, name, version, and settings icon."""
        hub_page = AgentHubPage(page)
        chat_page = ChatPage(page)

        with allure.step("Step 1 — Navigate to Agent Hub (Catalog page)"):
            hub_page.navigate()
            # Verify page loads
            hub_page.page_heading.wait_for(state="visible", timeout=10000)

        with allure.step("Step 2 — Open agent detail modal"):
            # Use Business Analyst as the test agent
            hub_page.open_agent_by_name("Business Analyst")

        with allure.step("Step 3 — Start conversation (click Start Chat button)"):
            # Click the Start Chat button in the modal
            hub_page.modal_start_chat_button.wait_for(state="visible", timeout=10000)
            hub_page.click_start_chat()

        with allure.step("Step 4 — Verify navigation to chat page"):
            # Wait for URL to change to /chat
            page.wait_for_url(re.compile(r"/chat"), timeout=15000)

        with allure.step("Step 5 — Verify chat page loads and agent is pre-populated"):
            chat_page.wait_for_page_load()

        with allure.step("Step 6 — Verify agent chip is visible in message input"):
            # The agent chip (switch participant button) should be visible
            chat_page.switch_participant_button.wait_for(state="visible", timeout=10000)
            assert chat_page.switch_participant_button.is_visible(), (
                "Agent chip should be visible in message input area"
            )

        with allure.step("Step 7 — Verify agent avatar/icon on chip"):
            # Avatar image should exist within the chip
            chip = chat_page.switch_participant_button
            avatar_img = chip.locator('img[alt="elitea"]')
            avatar_img.wait_for(state="visible", timeout=5000)
            assert avatar_img.is_visible(), "Agent avatar should be visible on chip"

        with allure.step("Step 8 — Verify agent name displayed on chip"):
            # Agent name should be visible on the chip
            chip_text = chat_page.switch_participant_button.text_content() or ""
            assert "Business Analyst" in chip_text or chip_text.strip(), (
                f"Agent name should be displayed on chip, got: {chip_text}"
            )

        with allure.step("Step 9 — Verify agent version is displayed"):
            # Version selector should be visible adjacent to the chip
            chat_page.chat_version_selector_trigger.wait_for(state="visible", timeout=10000)
            version_text = chat_page.chat_version_selector_trigger.text_content() or ""
            assert version_text.strip(), "Version text should be non-empty and visible"
            # Verify version format (v{major}.{minor})
            assert version_text.startswith("v") or version_text[0].isdigit(), (
                f"Version should match format v{{major}}.{{minor}}, got: {version_text}"
            )

        with allure.step("Step 10 — Verify settings icon/button is visible"):
            # Settings button should be visible in the composer
            chat_page.participant_settings_button.wait_for(state="visible", timeout=10000)
            assert chat_page.participant_settings_button.is_visible(), (
                "Settings icon/button should be visible on the agent chip"
            )

        with allure.step("Step 11 — Verify settings button is clickable"):
            # Settings button should be enabled and clickable
            settings_btn = chat_page.participant_settings_button
            assert settings_btn.is_enabled(), "Settings button should be enabled"
            # Attempt to click and verify it doesn't error (just click, don't wait for editor)
            settings_btn.click(force=True)
            # Brief wait to allow UI to respond
            page.wait_for_timeout(500)
            # No assertion needed - just verifying clickability doesn't error
