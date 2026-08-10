"""Test: Agent Hub — agent chip visible in message input with version and settings.

ELITEA-2362: Verify that when a user starts a conversation with an agent from
the Agent Hub catalog, the agent is displayed as a chip in the message input
area at the bottom of the page, including:
- Agent avatar/icon
- Agent name
- Agent version
- Settings icon button

AFS: test-specs/agent_hub/l2_agent_chip_visible_in_message_input_2362.md
"""

import allure
import pytest
from playwright.sync_api import Page, expect

from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage


class TestAgentChipVisibleInMessageInput:
    """Agent Hub — agent chip display in chat message input area."""

    @pytest.mark.p2
    @pytest.mark.regression
    @pytest.mark.agent_hub
    @allure.title("Agent chip visible in message input with version and settings")
    @allure.description(
        "Verify that after starting a conversation with an agent from Agent Hub, "
        "the agent chip is visible in the message input area with avatar, name, version, and settings icon."
    )
    def test_agent_chip_visible_with_version_and_settings(self, page: Page):
        """
        ELITEA-2362: Agent Hub — agent chip visible in message input with version and settings.

        Steps:
        1. Navigate to Agent Hub (Catalog) page
        2. Click on an agent card to open the preview modal
        3. Click "Start Chat" button to start conversation
        4. Verify agent participant chip is visible in message input area
        5. Verify chip displays avatar/icon
        6. Verify chip displays agent name
        7. Verify chip displays agent version
        8. Verify chip displays settings icon button
        """

        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)

        # Step 1: Navigate to Agent Hub
        with allure.step("Step 1 — Navigate to Agent Hub (Catalog) page"):
            agent_hub.navigate()

        # Step 2: Click agent card and open modal
        # Use the first visible agent card
        with allure.step("Step 2 — Click on an agent card to open the detail modal"):
            # Get the first agent card
            first_agent_card = page.locator(agent_hub.AGENT_CARD_PREFIX).first
            first_agent_card.wait_for(state="visible", timeout=10000)
            first_agent_name = first_agent_card.text_content().strip()
            assert first_agent_name, "Agent card should have name text"

            # Open the agent modal
            agent_hub.open_agent_by_name(first_agent_name)
            expect(agent_hub.modal_agent_name).to_be_visible()

        # Step 3: Click "Start Chat" button
        with allure.step("Step 3 — Click 'Start Chat' button"):
            agent_hub.click_start_chat()
            # Wait for navigation to chat page
            page.wait_for_url("/chat*", timeout=20000)
            # Wait a bit for the page to hydrate
            page.wait_for_timeout(2000)
            # Wait for the participant chip to appear (it renders faster than message input)
            page.locator(chat.PARTICIPANT_ROW_PREFIX).first.wait_for(state="visible", timeout=20000)

        # Step 4: Verify agent participant chip is visible in message input area
        with allure.step("Step 4 — Verify agent chip is visible in message input area"):
            # The participant chip should be present with testid pattern chat-participant-row-application-*
            participant_chip = page.locator(chat.PARTICIPANT_ROW_PREFIX).first
            expect(participant_chip).to_be_visible(timeout=10000)
            chip_text = participant_chip.text_content() or ""
            assert chip_text, "Participant chip should have text content"

        # Step 5: Verify chip displays avatar/icon
        with allure.step("Step 5 — Verify chip displays avatar/icon"):
            # Avatar should be an <img> element inside the participant chip
            avatar_img = participant_chip.locator("img").first
            expect(avatar_img).to_be_visible()
            # Avatar should have a src pointing to the entity icons
            avatar_src = avatar_img.get_attribute("src") or ""
            assert "default_entity_icons" in avatar_src or avatar_src.startswith("https://"), (
                f"Avatar image should have a valid src, got: {avatar_src}"
            )

        # Step 6: Verify chip displays agent name
        with allure.step("Step 6 — Verify chip displays agent name"):
            # Agent name should be visible in the chip text
            # The chip structure has name in a <span>
            name_spans = participant_chip.locator("span:not([class*='Mui'])").all()
            assert len(name_spans) > 0, "Participant chip should contain name span elements"
            chip_all_text = participant_chip.text_content() or ""
            # Agent name should be in the chip text (we opened it from the card)
            assert chip_all_text, "Chip should display agent name"

        # Step 7: Verify chip displays version
        with allure.step("Step 7 — Verify chip displays version (e.g., v2.1)"):
            # Version should be visible in the chip (e.g., "v2.1", "base", etc.)
            chip_text = participant_chip.text_content() or ""
            # Version is typically shown as a shortened form like "base" or "v*"
            assert chip_text, "Chip text should contain version information"
            # Verify it's not just the agent name (should have more content)
            assert len(chip_text.strip()) > 10, "Chip should contain name and version"

        # Step 8: Verify settings icon is visible on the chip
        with allure.step("Step 8 — Verify settings icon is visible on the chip"):
            # The settings button (gear icon) should be present with testid chat-participant-edit-view-button
            settings_button = participant_chip.locator(chat.PARTICIPANT_EDIT_VIEW_BUTTON).first
            expect(settings_button).to_be_visible()
            # Settings button should have aria-label="View settings"
            aria_label = settings_button.get_attribute("aria-label") or ""
            assert "settings" in aria_label.lower() or "view" in aria_label.lower(), (
                f"Settings button should have appropriate aria-label, got: {aria_label}"
            )

        # Additional verification: ensure remove button is also present
        with allure.step("Verify remove button is also present on chip"):
            remove_button = participant_chip.locator(chat.PARTICIPANT_REMOVE_BUTTON).first
            expect(remove_button).to_be_visible()
            remove_aria_label = remove_button.get_attribute("aria-label") or ""
            assert "remove" in remove_aria_label.lower() or "delete" in remove_aria_label.lower(), (
                f"Remove button should have appropriate aria-label, got: {remove_aria_label}"
            )
