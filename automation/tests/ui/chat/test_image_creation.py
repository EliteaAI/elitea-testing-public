"""UI Tests for Chat Image Creation functionality.

Tests the image generation capability in Elitea chat using the Image Creation
internal tool with the project's DEFAULT model.

TMS case ELITEA-0679 names no model: its precondition is "at least one shared
image model is available as the default" and Step 3 sends the prompt "using the
default image model". The test therefore selects no model at all.

History: the test used to call select_model("GPT-5.2") first. That model was
removed from every working project's catalog (see #2117), so the call timed out
(card #2112). It was a test artifact the case never asked for; naming any
replacement literal would just re-break on the next catalog change.

User Flow:
1. Enable "Image Creation" in internal tools
2. Describe the image to generate
3. Receive generated image in chat

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
        """Create image from text prompt and verify image appears in response.

        Uses the project's DEFAULT model — ELITEA-0679 Step 3 specifies "using the
        default image model" and the case names no model. No model is selected.
        """
        with allure.step("Step 1 — Navigate to chat"):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step("Step 2 — Enable Image Creation internal tool"):
            chat.enable_image_creation(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.is_image_creation_enabled(timeout=UI_ELEMENT_TIMEOUT), (
                "Image Creation tool should be toggled ON after enabling it"
            )

        with allure.step(f"Step 3 — Send image generation prompt: {prompt[:50]}..."):
            initial_count = chat.get_message_count()
            chat.send_message(prompt, use_enter=True)

        with allure.step("Step 4 — Wait for AI response with image"):
            chat.wait_for_input_ready()
            chat.wait_for_ai_response(initial_count=initial_count, timeout=IMAGE_GENERATION_TIMEOUT)
            chat.wait_for_image_in_response(timeout=IMAGE_GENERATION_TIMEOUT)

        with allure.step("Step 5 — Verify image appears in response"):
            assert chat.get_images_in_last_message() >= 1, (
                "Expected at least one image in the AI response"
            )
            assert chat.get_generated_image_src(), (
                "Generated image should have a valid non-empty source URL"
            )
