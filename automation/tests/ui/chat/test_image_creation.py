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
from pages.chat_page import ChatPage

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
    def test_create_image(self, page, conversation_id, prompt):
        """Create image from text prompt and verify image appears in response.

        User flow: Select GPT-5.2 → Enable image creation → Send prompt → Get image
        """
        chat = ChatPage(page)
        chat.navigate_to_chat(conversation_id=conversation_id)

        # Select model first — switching models resets internal tool toggles
        chat.select_model("GPT-5.2", timeout=UI_ELEMENT_TIMEOUT)
        chat.enable_image_creation(timeout=UI_ELEMENT_TIMEOUT)

        initial_count = chat.get_message_count()
        chat.send_message(prompt, use_enter=True)

        chat.wait_for_input_ready()
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
        chat.wait_for_image_in_response(timeout=IMAGE_GENERATION_TIMEOUT)

        assert chat.get_images_in_last_message() >= 1, (
            "Expected at least one image in the AI response"
        )
        assert chat.get_generated_image_src(), (
            "Generated image should have a valid non-empty source URL"
        )
