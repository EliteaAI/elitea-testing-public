"""UI Tests for Chat Image Creation functionality.

Tests the image generation capability in Elitea chat using the Image creation
internal tool with GPT-5.2 model.

User Flow:
1. Select GPT-5.2 model
2. Enable "Image creation" in internal tools (after model switch to avoid reset)
3. Describe the image to generate
4. Receive generated image in chat

Markers:
    - ui: requires browser
    - p1: high priority tests
    - p2: medium priority tests
    - chat: chat-related tests
    - slow: slow tests (image generation can take 60-120s)

Usage:
    cd automation
    pytest tests/ui/chat/test_image_creation.py -v
"""

import pytest
from pages.chat_page import ChatPage, FeatureNotAvailableError
import allure

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.slow]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
IMAGE_GENERATION_TIMEOUT = 180000  # Image generation can take 60-120s; 180s gives comfortable margin
AI_RESPONSE_TIMEOUT = 30000        # Time for AI response container to appear in DOM
UI_ELEMENT_TIMEOUT = 10000         # UI elements


class TestImageCreation:
    """Tests for chat image creation functionality."""

    @pytest.mark.parametrize("prompt", [
        pytest.param(
            "Generate an image of a sunset over mountains",
            marks=pytest.mark.p1,
            id="detailed_description",
        ),
        pytest.param(
            "Create an image of a red apple.",
            marks=pytest.mark.p2,
            id="minimal_prompt",
        ),
    ])
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/image-generation/ELITEA-0679_image-creation-internal-tool-happy-path-image-generated-successfully-i.md", "onetest-ai Test Case link")
    def test_create_image(self, page, conversation_id, prompt):
        """Create image from text prompt and verify image appears in response."""
        with allure.step("Step 1 — Navigate to chat"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Select GPT-5.2 model"):
            chat.select_model("GPT-5.2", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Enable Image creation internal tool"):
            try:
                chat.enable_image_creation(timeout=UI_ELEMENT_TIMEOUT)
            except FeatureNotAvailableError:
                pytest.skip(
                    "Internal tools toggle not available — image creation feature "
                    "may have been moved or removed in current UI version"
                )

        with allure.step(f"Step 4 — Send image generation prompt: {prompt[:50]}..."):
            initial_count = chat.get_message_count()
            chat.send_message(prompt, use_enter=True)

        with allure.step("Step 5 — Wait for AI response with image"):
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
            chat.wait_for_image_in_response(timeout=IMAGE_GENERATION_TIMEOUT)

        with allure.step("Step 6 — Verify image appears in response"):
            assert chat.get_images_in_last_message() >= 1, (
                "Expected at least one image in the AI response"
            )
            assert chat.get_generated_image_src(), (
                "Generated image should have a valid non-empty source URL"
            )
