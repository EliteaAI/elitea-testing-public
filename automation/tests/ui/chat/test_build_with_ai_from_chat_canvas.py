"""UI Test for ELITEA-1920 — Build with AI from the in-chat AgentEditor canvas.

Verifies the complete end-to-end "Build with AI" flow when triggered from
the in-chat "+ Create New Agent" canvas (rather than the standalone
``/agents/create`` page): opening the canvas, opening the generation modal,
generating a draft, approving it, and confirming the newly created agent is
added as a participant in the CURRENT conversation (no navigation away from
``/chat``) and is immediately visible in the Participants list.

Spec: test-specs/chat-interface/l2_build-with-ai-from-chat-canvas-adds-participant_ELITEA-1920.md

Coverage boundary (AFS § Coverage decision): the canvas-open shell (steps
1-2) and post-save participant listing (steps 8-9) are already proven, for a
MANUALLY-filled agent, by ``test_create_agent_via_chat_canvas.py``
(ELITEA-2166). The Build-with-AI generate/review/approve flow itself (steps
3-7) is already proven from a DIFFERENT host page (``/agents/create``) by
``test_agent_build_with_ai.py`` (ELITEA-1907/1909/1911/1915). What is
genuinely new here — and the sole reason this is its own test rather than an
extension of either — is the completion wiring: from the chat canvas,
``onAgentCreated`` is ``useAgentCreation.js``'s hook, which turns the created
agent into a chat participant and stays on ``/chat`` entirely, instead of
navigating to ``/agents/all/{id}`` (ELITEA-1909's documented behavior for the
``/agents/create`` flow). No new page-object locators or testids were needed
(100% reuse of ``ChatPage``, ``AgentCanvasPage``, ``GenerateAgentModalPage``) —
this is a new, small test module composing all three, mirroring how
``test_agent_with_toolkit_chat.py`` composes ``AgentPage`` + ``ChatPage`` for
a similar cross-cutting scenario.

Step 6's "select suggested resources" sub-step is deliberately NOT exercised
here — it is the own, already-covered subject of ELITEA-1907/1909/1911
(entity-generic, not chat-specific); re-deriving it here would duplicate
coverage without adding anything chat-specific (AFS step 5 rationale).
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from pages.agent_canvas_page import AgentCanvasPage
from pages.chat_page import ChatPage
from pages.generate_agent_modal_page import GenerateAgentModalPage

logger = logging.getLogger("elitea.tests.chat.build_with_ai")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.agents, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
# The generate-draft call is a real (non-mocked) LLM call — a longer,
# more generous timeout than a mocked-response test avoids flaking on
# ordinary LLM-latency variance (same rationale as
# LIVE_GENERATE_RESPONSE_TIMEOUT in test_agent_build_with_ai.py).
LIVE_GENERATE_RESPONSE_TIMEOUT = 30_000

# Arbitrary, per the case's own Test Data table ("Any valid agent
# description") — not verbatim from the case, which gives no exact wording.
PROMPT_TEXT = (
    "An agent that summarizes GitHub pull request descriptions into a "
    "single concise sentence."
)


class TestBuildWithAIFromChatCanvas:
    """ELITEA-1920: Build with AI from the in-chat AgentEditor canvas — the
    generated agent is added as a chat participant without navigating away
    from the current conversation (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-1920_build-with-ai-from-chat-canvas-adds-participant.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_build_with_ai_from_chat_canvas_adds_participant(self, page, agent_api):
        """Generate an agent via Build with AI from the in-chat canvas;
        verify it's created without navigating away from /chat, is added as
        a participant, and is visible in the Participants list.

        Steps (AFS
        test-specs/chat-interface/l2_build-with-ai-from-chat-canvas-adds-participant_ELITEA-1920.md):
        1. + Chat -> + menu -> Agents -> + Create New Agent. Verify the
           canvas opens with heading "Create New Agent".
        2. Click "Build with AI"; verify the GenerateAgentModal opens.
        3. Fill the prompt, click Generate; verify the generate-draft POST
           resolves 200.
        4. Verify the modal transitions to the populated review form, and
           the Name/Description/Instructions fields are actually
           pre-populated (UI-level assertion via GenerateAgentModalPage's
           review_name_input/review_description_input/review_instructions_
           input, added for this AFS's field-population claim).
        5. (Suggested-resource selection intentionally not exercised — see
           module docstring.)
        6. Click "Create Agent"; verify the creation POST resolves 201 and
           the canvas stays on /chat (no navigation to /agents/all/{id}),
           transitioning its heading to the created agent's name.
        7. Open the PARTICIPANTS panel; verify it lists the created agent.
        """
        chat = ChatPage(page)
        agent_canvas = AgentCanvasPage(page)
        modal = GenerateAgentModalPage(page)

        agent_id = None
        try:
            with allure.step("Setup — navigate to chat and open a fresh conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 1 — + menu -> Agents -> + Create New Agent; verify "
                "the canvas panel opens with heading 'Create New Agent'"
            ):
                chat.open_create_new_agent_canvas(timeout=NAVIGATION_TIMEOUT)
                agent_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                expect(agent_canvas.title).to_have_text(
                    "Create New Agent", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                'Step 2 — Click "Build with AI"; verify the GenerateAgentModal opens'
            ):
                modal.open_modal(timeout=UI_ELEMENT_TIMEOUT)
                expect(modal.modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Enter the prompt and click Generate; verify the "
                "generate-draft request resolves 200"
            ):
                modal.fill_prompt(PROMPT_TEXT)
                assert modal.get_prompt_value() == PROMPT_TEXT, (
                    "Prompt textarea should contain exactly the entered text"
                )

                generate_response = modal.click_generate_and_wait_for_response(
                    timeout=LIVE_GENERATE_RESPONSE_TIMEOUT
                )
                assert generate_response.status == 200, (
                    f"Expected the generate-draft request to succeed, got "
                    f"{generate_response.status}"
                )

            with allure.step(
                "Step 4 — Verify the modal transitions from loading to a "
                "populated review form, and the Name/Description/"
                "Instructions fields are actually pre-populated in the UI "
                "(case step 5's exact claim — a real UI-level assertion, "
                "not just the network response body)"
            ):
                modal.wait_for_review_form(timeout=LIVE_GENERATE_RESPONSE_TIMEOUT)
                draft = generate_response.json()
                generated_name = draft.get("name")
                assert generated_name, (
                    f"Generate-draft response should include a non-empty "
                    f"name field, got: {draft!r}"
                )

                expect(modal.review_name_input).to_have_value(
                    generated_name, timeout=UI_ELEMENT_TIMEOUT
                )
                assert modal.get_review_description(), (
                    "Review-form Description field should be pre-populated "
                    "from the generated draft, got an empty value"
                )
                assert modal.get_review_instructions(), (
                    "Review-form Instructions field should be pre-populated "
                    "from the generated draft, got an empty value"
                )

            with allure.step(
                'Step 6 — Click "Create Agent"; verify the creation POST '
                "resolves 201 and the canvas stays on /chat (no navigation "
                "to /agents/all/{id}, contrast with the /agents/create "
                "flow's ELITEA-1909-documented auto-navigation), heading "
                "transitioning to the created agent's name"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/elitea_core/applications/prompt_lib/" in r.url
                ) as resp_info:
                    modal.approve_button.click()
                create_response = resp_info.value
                assert create_response.status == 201, (
                    f"Agent-creation POST should resolve 201, got "
                    f"{create_response.status} for {create_response.url}"
                )
                created_agent = create_response.json()
                agent_id = created_agent.get("id")
                assert agent_id, (
                    f"Expected a numeric agent id in the creation response, "
                    f"got: {created_agent!r}"
                )
                created_agent_name = created_agent.get("name")

                page.wait_for_url(
                    re.compile(rf"/chat\?edited_participant_id={agent_id}\b"),
                    timeout=UI_ELEMENT_TIMEOUT,
                )
                assert "/agents/all/" not in page.url, (
                    f"Should stay on /chat, not navigate to the agent's own "
                    f"detail page — got {page.url}"
                )

                expect(agent_canvas.title).to_have_text(
                    created_agent_name, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Open the PARTICIPANTS panel; verify the AGENTS "
                "section lists the created agent"
            ):
                popper = chat.open_participants_popover(
                    timeout=UI_ELEMENT_TIMEOUT, section="agents"
                )
                expect(popper).to_contain_text(
                    created_agent_name, timeout=UI_ELEMENT_TIMEOUT
                )
        finally:
            with allure.step("Cleanup — delete the created agent"):
                # No conversation cleanup: this test never sends a message,
                # so the conversation never acquires a server-side id (same
                # "unsaved until first message" behavior ELITEA-2166's AFS
                # documents) — nothing to delete (AFS § Cleanup).
                if agent_id:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Deleted agent %s", agent_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for agent %s: %s", agent_id, exc
                        )
