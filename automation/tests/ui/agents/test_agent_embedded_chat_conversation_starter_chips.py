"""Conversation starter chips appear in the embedded chat panel and are
clickable (ELITEA-1886).

Adds two conversation starters to a dedicated agent via the "Chat starters"
accordion (agent form), Saves, reloads for a pristine embedded-chat mount,
verifies both starter chips render before any message is sent, clicks one
chip (pre-fill only — no auto-send, chip row disappears immediately), then
explicitly sends via `chat-send-button` and verifies the agent responds.

Test-data strategy (per AFS, adjusted during implementation): a dedicated,
uniquely-named agent is created per-test via the plain `AgentAPI.create_agent()`
(matches `test_agent_embedded_chat_send_message.py`'s already-proven pattern for
an actual embedded-chat predict round trip — `_default_llm_settings()`'s
`reasoning_effort: "medium"` / `temperature: null` combo, the documented "match
UI default" shape). A live-exploration probe during this case's implementation
(against the shared fixture agent `elitea-1736-conversation-agent`, id 6732,
restored afterward) showed the `reasoning_effort: "none"` payload shape used by
`test_agent_remove_variable.py` (a save/reload-only test that never exercises an
actual predict) leaves the composer populated but produces NO
`POST .../conversations/...` when Send is clicked — that combo is safe for
Save-only tests but not proven for a real chat round trip, so this test does not
reuse it. Starters are added via the live UI form (steps 1-3 are literal UI
actions matching the case text), not pre-populated in the creation payload, so
Step 2's per-field input-value + character-counter assertions have something to
observe. `press_sequentially` is used (not `fill()`) — the project's standard
for MUI React-controlled inputs, and what the character-counter's live update
depends on (`.claude/rules/mui-patterns.md`).

The starter-chip element itself
(`ChatConversationStarters.jsx`'s `EllipsisTextWithTooltip` call site) had no
testid before this case — `testId="chat-conversation-starter-tile"` was added
via `add-data-testid` (EliteaAI/EliteaUI, `automation/testids`), reusing the
literal already wired on the sibling `/chat/{id}` call site
(`NewConversationView.jsx`, ELITEA-2369) since the two call sites never render
simultaneously. See `AgentDetailPage.CHAT_STARTER_TILE` / `get_chat_starter_tiles()`
/ `click_chat_starter_tile()` (added alongside `ChatPage`'s identical-shape
counterpart).

Spec: test-specs/agents/l2_conversation-starter-chips-visible-and-clickable_ELITEA-1886.md
"""

import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from playwright.sync_api import Page, Response

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_RESPONSE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

STARTER_1 = "How do I create a new agent?"
STARTER_2 = "What toolkits are available?"


def _is_save_response(response: Response) -> bool:
    """Check if response is an agent save PUT request."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


# Known defect #554 (already filed, unrelated) — an RTK-Query timing race in
# EliteaUI/src/api/toolkits.js's `toolkitTypes` endpoint fires before
# `useSelectedProjectId()` resolves, building the URL with an empty
# projectId segment (".../toolkits/prompt_lib/") which 404s. Intermittent
# (client-side race, not deterministic) and unrelated to the conversation-
# starter-chips flow this filter is applied to — applied defensively (this
# test navigates a full agent-detail page load, the same trigger condition
# #554 documents as reproducible on "any page render"), matching the
# batch's own hardening-gate findings (elitea-testing-public#1277). SAME
# filter technique already established in test_credential_search_by_name.py
# / test_agent_publish_unpublish_version.py — matched on msg.location.url
# containing the toolkits endpoint path, NOT a blanket "any 404" filter, so
# an unrelated 404 from a genuinely different resource still surfaces as a
# real, unexpected failure.
#
# NOTE: applied at the assertion site (below), not inside
# ``AgentDetailPage.capture_console_errors()`` — that helper is shared
# base_page.py code with 30+ callers across the whole suite, well outside
# this batch's scope; filtering only the collected list here keeps the
# change additive and confined to this file.
def _is_known_554_toolkits_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


class TestConversationStarterChipsVisibleAndClickable:
    """Conversation starter chips visible before any message + clickable
    (ELITEA-1886, p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agents/ELITEA-1886_conversation-starter-chips-appear-in-chat-panel-and-are-clickable.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_conversation_starter_chips_visible_and_clickable(self, page: Page, agent_api):
        """Both configured starters render as chips in the embedded chat
        before any message, clicking one pre-fills the input (no auto-send,
        chip row disappears immediately), and explicitly sending it produces
        a real agent response."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1886-starters-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent(
                agent_name,
                "Auto-created for ELITEA-1886 conversation starter chips test",
                "You are a test agent.",
            )
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        console_errors = detail_page.capture_console_errors()
        failed_responses: list[int] = []
        page.on(
            "response",
            lambda resp: failed_responses.append(resp.status) if resp.status >= 400 else None,
        )

        try:
            with allure.step("Step 1 — Navigate to the agent detail page"):
                detail_page.navigate(agent_id)
                assert detail_page.information_section.is_visible(), (
                    "Agent detail page's Information section should be visible"
                )

            with allure.step(
                'Step 2 — Add starters "How do I create a new agent?" and '
                '"What toolkits are available?" via press_sequentially'
            ):
                inputs = detail_page.conversation_starter_inputs

                detail_page.add_conversation_starter()
                inputs.nth(0).press_sequentially(STARTER_1, delay=10)
                assert inputs.nth(0).input_value() == STARTER_1, (
                    f"First starter input should read {STARTER_1!r}, got {inputs.nth(0).input_value()!r}"
                )
                counter_1 = detail_page.get_conversation_starter_counter_text(index=0)
                assert counter_1, "Character counter should update for the first starter field"

                detail_page.add_conversation_starter()
                inputs.nth(1).press_sequentially(STARTER_2, delay=10)
                assert inputs.nth(1).input_value() == STARTER_2, (
                    f"Second starter input should read {STARTER_2!r}, got {inputs.nth(1).input_value()!r}"
                )
                # The counter only renders for the currently-FOCUSED field
                # (ConversationStarters.jsx's `isFocused(...) && value.length > 0`
                # ternary) — at any moment there is at most one counter element
                # in the DOM, so it is always at position 0 of the rendered
                # counters collection regardless of which starter field it
                # belongs to (confirmed live; matches the existing
                # single-field usage in test_agent_character_limits.py).
                counter_2 = detail_page.get_conversation_starter_counter_text(index=0)
                assert counter_2, "Character counter should update for the second starter field"

            with allure.step("Step 3 — Click Save"):
                assert detail_page.is_save_enabled(), "Save should be enabled once the form is dirty"
                with page.expect_response(_is_save_response, timeout=SAVE_RESPONSE_TIMEOUT) as resp_info:
                    detail_page.click_save(timeout=UI_ELEMENT_TIMEOUT)
                save_response = resp_info.value
                assert save_response.status == 201, (
                    f"PUT application/prompt_lib/... should return 201 on Save, got {save_response.status}"
                )

            with allure.step(
                "Step 4 — Open a new chat session with this agent (full-navigation "
                "reload for a pristine, freshly-mounted embedded chat panel)"
            ):
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_chat_message_count() == 0, (
                    "Embedded chat should have no messages before any is sent"
                )

            with allure.step(
                "Step 5 — Verify both starter chips are visible in the chat panel "
                "before any message is sent"
            ):
                detail_page.get_chat_starter_tiles().first.wait_for(
                    state="visible", timeout=NAVIGATION_TIMEOUT
                )
                tile_count = detail_page.get_chat_starter_tiles().count()
                assert tile_count == 2, f"Expected 2 starter chips in the embedded chat, got {tile_count}"
                tile_texts = [
                    (detail_page.get_chat_starter_tiles().nth(i).text_content() or "").strip()
                    for i in range(tile_count)
                ]
                assert STARTER_1 in tile_texts, f"{STARTER_1!r} chip should be visible, got: {tile_texts}"
                assert STARTER_2 in tile_texts, f"{STARTER_2!r} chip should be visible, got: {tile_texts}"
                assert detail_page.get_chat_message_count() == 0, (
                    "No message should be present while the starter chips are showing"
                )

            with allure.step(f"Step 6 — Click the {STARTER_1!r} starter chip"):
                clicked_text = detail_page.click_chat_starter_tile(STARTER_1, timeout=UI_ELEMENT_TIMEOUT)
                assert clicked_text == STARTER_1, (
                    f"Clicked chip's own text should equal {STARTER_1!r}, got {clicked_text!r}"
                )

            with allure.step(
                "Step 7 — Verify the starter text is submitted as a pre-filled "
                "value in the input (pre-fill only — no auto-send, chip row "
                "disappears immediately)"
            ):
                assert detail_page.chat_message_input.input_value() == STARTER_1, (
                    f"Chat input should be pre-filled with {STARTER_1!r}, got "
                    f"{detail_page.chat_message_input.input_value()!r}"
                )
                assert detail_page.get_chat_starter_tiles().count() == 0, (
                    "Starter chip row should disappear immediately once a chip is clicked"
                )
                assert detail_page.get_chat_message_count() == 0, (
                    "No message should be sent by the chip click alone (pre-fill only)"
                )

            initial_count = detail_page.get_chat_message_count()
            with allure.step(
                "Step 8 — Send the pre-filled message and verify the agent responds"
            ):
                detail_page.chat_send_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                # force=True — same MUI-overlay-interception workaround the
                # sibling starter-flow test uses (ELITEA-2369,
                # test_agent_hub_start_conversation_with_starters.py Step 14).
                detail_page.chat_send_button.click(force=True)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                assert detail_page.get_chat_message_count() > initial_count, (
                    "Message count should increase after sending the pre-filled starter"
                )
                response_text = detail_page.get_last_chat_response_text()
                assert response_text != "", "Agent response should be non-empty"

            unexpected_console_errors = [
                m for m in console_errors if not _is_known_554_toolkits_404(m)
            ]
            assert not unexpected_console_errors, (
                "Unexpected console errors during the run: "
                f"{[m.text for m in unexpected_console_errors]}"
            )
            assert not failed_responses, f"Unexpected 4xx/5xx responses: {failed_responses}"
        finally:
            console_errors.stop()
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
