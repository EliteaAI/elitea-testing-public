"""UI Tests for ELITEA-2184 / ELITEA-2187 / ELITEA-2185 — Chat: Regenerate
action-icon exclusivity (family) and click-replace flow.

ELITEA-2184 and ELITEA-2187 are a **family** (same live contract, same
setup shape — see ``test-specs/chat-interface/l2_regenerate-visible-and-
exclusive-to-last-response_ELITEA-2184_2187.md``): the ``chat-regenerate-
button``/``chat-delete-button`` testids exist in the DOM ONLY for the
message where ``isLastMessage`` is true, while ``chat-copy-button``/
``chat-read-out-button`` exist on every AI message. ELITEA-2187 adds one
extra observable beyond ELITEA-2184: clicking Regenerate on the last
response actually triggers a new generation.

ELITEA-2185 is its own case: clicking Regenerate replaces the last
message's content IN PLACE with a genuinely new LLM-produced response,
while the user's own message and the message-item count stay unchanged.

ELITEA-2186 ("Regenerate After Stopped Generation") is NOT implemented
here — see ``test-specs/chat-interface/l2_regenerate-after-stopped-
generation_ELITEA-2186.md`` (status ``blocked``): its own precondition (a
stopped response to hover over and regenerate) cannot be constructed
against the live product while known defect
https://github.com/EliteaAI/elitea-testing-public/issues/1569 ("Stop wipes
the entire message exchange, not just the streaming response") is open.

Two new page-object constants were required (``ChatPage.REGENERATE_ACTION_
BUTTON`` / ``DELETE_ACTION_BUTTON`` / ``COPY_ACTION_BUTTON`` / ``READ_OUT_
ACTION_BUTTON``): the pre-existing ``regenerate_action_button`` etc.
``LocatorDescriptor`` fields resolve PAGE-WIDE, which throws a Playwright
strict-mode violation once 2+ AI messages share the (non-exclusive)
Copy/Read-out testid.

Substitution declaration: none — every observable (Send, hover, the
action-icon testids, the Regenerate click, the resulting new generation,
message counts/text) is produced and read live against the real DEV
backend; no ``page.route``/``page.evaluate``/mock is used (AFS §
Fidelity Declaration).
"""

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 15_000
# Generous ceiling for a full generation/regeneration to complete. Short
# prompts like the ones this file uses ("Hi", "Hi again", ...) complete in
# single-digit seconds in this environment (confirmed live — none invoke the
# file-writing tool that makes longer/creative prompts take 34-54s, per
# .agents/testing.md's own note on the "write a poem" family) — kept at the
# project's standard generous value for CI headroom.
AI_RESPONSE_TIMEOUT = 120_000


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_streaming_response.py`` / other chat suite files —
    a ``403`` on ``GET .../secrets/secrets/default/{project_id}`` fires on
    every page load in this local environment regardless of the action
    taken, and is unrelated to the regenerate flow under test.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestRegenerateResponse:
    """Chat message action row: Regenerate exclusivity (ELITEA-2184/2187) and click-replace flow (ELITEA-2185)."""

    # -----------------------------------------------------------------
    # Suite-local helpers (Hard Rule 7) — shared by all three tests below.
    # -----------------------------------------------------------------
    def _send_and_wait(self, chat: ChatPage, text: str) -> int:
        """Send *text*, wait for its AI response to complete.

        Returns the AI response's message-item index (``initial_count + 1``).
        """
        initial_count = chat.get_message_count()
        chat.send_message(text)
        chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)
        return initial_count + 1

    def _wait_for_regeneration_complete(self, chat: ChatPage, timeout: int = AI_RESPONSE_TIMEOUT):
        """Wait for a Regenerate-triggered in-place update to finish.

        Unlike a fresh Send (which APPENDS a new message — see
        ``wait_for_ai_response``), Regenerate replaces the last message's
        content IN PLACE, so there is no new list index to wait on.
        Completion signal: the Stop control (reused, identical testid to a
        normal Send's mid-stream state — confirmed live) leaves the
        composer's send-slot.
        """
        expect(chat.stop_generation_button).to_have_count(0, timeout=timeout)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2184_chat-regenerate-button-visible-on-last-llm-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_regenerate_visible_only_on_last_response(self, page, conversation_id):
        """ELITEA-2184: Chat – Regenerate Button Visible on Last LLM Response (l2, high).

        Steps (AFS test-specs/chat-interface/l2_regenerate-visible-and-
        exclusive-to-last-response_ELITEA-2184_2187.md, family with
        ELITEA-2187 — this test covers ELITEA-2184's own scope only):
        1. Send 2 short messages sequentially so both an "earlier" and a
           "last" AI response exist.
        2. Hover the last response; verify Regenerate + the full 4-icon
           action row (speaker, copy, regenerate, delete) are visible.
        3. Hover an earlier (non-last) response; verify Regenerate is
           absent, scoped to that specific message.
        4. Verify Regenerate is exclusive to the last response via a
           DOM-wide testid count (deterministic — proves the element does
           not exist for earlier messages, not merely that it isn't
           currently hovered/painted).
        """
        chat = ChatPage(page)
        console_issues = []
        page_errors = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step(
            "Setup — navigate to the fresh conversation; send 2 short "
            "messages so an earlier AND a last AI response both exist"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            earlier_ai_index = self._send_and_wait(chat, "Hi")
            last_ai_index = self._send_and_wait(chat, "Hi again")

        with allure.step(
            "Steps 1/2/4 — Hover the last response; verify Regenerate and "
            "the full action-icon row (speaker, copy, regenerate, delete) "
            "are visible"
        ):
            last_message = chat.messages_container.nth(last_ai_index)
            last_message.scroll_into_view_if_needed()
            last_message.hover()
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(last_message.locator(chat.READ_OUT_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(last_message.locator(chat.COPY_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(last_message.locator(chat.DELETE_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 3 — Hover an earlier (non-last) response; verify no "
            "Regenerate button, scoped to that specific message"
        ):
            earlier_message = chat.messages_container.nth(earlier_ai_index)
            earlier_message.scroll_into_view_if_needed()
            earlier_message.hover()
            expect(earlier_message.locator(chat.REGENERATE_ACTION_BUTTON)).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 4 — Verify Regenerate is exclusive to the last response "
            "(DOM-wide testid count == 1, located inside the last message)"
        ):
            regenerate_count = chat.regenerate_action_button.count()
            assert regenerate_count == 1, (
                "Expected exactly 1 chat-regenerate-button in the DOM "
                f"(last-message-exclusive by product design), got {regenerate_count}"
            )
            assert last_message.locator(chat.REGENERATE_ACTION_BUTTON).count() == 1, (
                "The single Regenerate button should be inside the LAST "
                "message, not elsewhere in the conversation"
            )

        with allure.step("Side-channel check — no unexpected console/JS errors"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2187_chat-regenerate-is-only-available-on-the-last-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_regenerate_only_on_last_and_click_triggers_new_generation(
        self, page, conversation_id
    ):
        """ELITEA-2187: Chat – Regenerate Is Only Available on the Last
        Response Not on Earlier Messages (l2, high).

        Steps (AFS test-specs/chat-interface/l2_regenerate-visible-and-
        exclusive-to-last-response_ELITEA-2184_2187.md, family with
        ELITEA-2184 — this test covers ELITEA-2187's own scope, including
        the click step ELITEA-2184 does not have):
        1. Send 3 short messages sequentially (case's own precondition:
           "at least 3 message-response pairs").
        2. Hover an earlier (non-last) response; verify no Regenerate.
        3. Hover the last response; verify Regenerate is visible.
        4. Click Regenerate on the last response; verify a new generation
           is genuinely triggered (the Stop control occupies the
           composer's send-slot — reused, identical signal to a normal
           Send's mid-stream state, confirmed live) — and, as a HARD
           assertion (fix round 1, review finding), that the regenerated
           text genuinely differs from the pre-regenerate text, so a no-op
           Regenerate cannot pass green — then wait for it to complete and
           verify the action row is restored — left in a clean,
           deterministic end state rather than an in-flight generation
           (AFS § Axis 2 addition).
        """
        chat = ChatPage(page)
        console_issues = []
        page_errors = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step(
            "Setup — navigate to the fresh conversation; send 3 short "
            "messages (case's own 'at least 3 message-response pairs' "
            "precondition)"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            first_ai_index = self._send_and_wait(chat, "Hi")
            self._send_and_wait(chat, "Hi again")
            last_ai_index = self._send_and_wait(chat, "One more hello")

        with allure.step(
            "Step 1 — Hover an earlier (non-last) response; verify no "
            "Regenerate text button, scoped to that specific message"
        ):
            earlier_message = chat.messages_container.nth(first_ai_index)
            earlier_message.scroll_into_view_if_needed()
            earlier_message.hover()
            expect(earlier_message.locator(chat.REGENERATE_ACTION_BUTTON)).to_have_count(
                0, timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            "Step 2 — Hover the last response; verify Regenerate button "
            "and regenerate icon are visible"
        ):
            last_message = chat.messages_container.nth(last_ai_index)
            last_message.scroll_into_view_if_needed()
            last_message.hover()
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 3 — Click Regenerate on the last response; verify a new "
            "generation is genuinely triggered (Stop control occupies the "
            "composer's send-slot)"
        ):
            pre_click_body = chat._extract_message_body(last_message)
            chat.regenerate_action_button.click()
            expect(chat.stop_generation_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Wait for the triggered regeneration to complete; verify the "
            "action row is restored on the (still-last) message"
        ):
            self._wait_for_regeneration_complete(chat)
            last_message.scroll_into_view_if_needed()
            last_message.hover()
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            post_click_body = chat._extract_message_body(last_message)
            assert post_click_body and post_click_body.strip(), (
                "Regenerated response should be non-empty coherent content, "
                f"got: {post_click_body!r}"
            )
            # Hard assertion (fix round 1, review finding): a Regenerate that
            # no-ops and resurfaces the cached/identical text must FAIL this
            # test, not merely log a warning — "click triggers a genuinely
            # new generation" is this step's own claim (case text: "New
            # generation triggered correctly"). A demoted `logger.warning`
            # here is the No Defect Masking Rule's forbidden "demote expect()
            # to log.info" shape regardless of how the AFS's Axis 2 framed
            # the flake-avoidance rationale — see `.agents/testing.md`'s
            # Fidelity policy ("the response is the oracle") for why the
            # invariant itself must be asserted, not merely observed. A rare
            # coincidental identical LLM repeat on a short, open-ended greeting
            # prompt ("Hi"/"Hi again"/"One more hello") is accepted ordinary
            # test flakiness, not masking — an occurrence here is signal to
            # investigate (real no-op regression vs. genuine LLM coincidence),
            # never something to silently swallow.
            assert post_click_body != pre_click_body, (
                "Regenerated response text is identical to the pre-regenerate "
                "text — Regenerate should trigger a genuinely NEW LLM "
                f"completion, not resurface cached/identical content: {post_click_body!r}"
            )

        with allure.step("Side-channel check — no unexpected console/JS errors"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2185_chat-clicking-regenerate-generates-new-response.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_regenerate_replaces_response_with_new_generation(self, page, conversation_id):
        """ELITEA-2185: Chat – Clicking Regenerate Generates a New Response
        Based on Previous User Input (l2, high).

        Steps (AFS test-specs/chat-interface/l2_regenerate-replaces-
        response-with-new-generation_ELITEA-2185.md):
        1. Send a message; hover the completed response; verify Regenerate
           is visible.
        2. Click Regenerate; verify the previous response is replaced IN
           PLACE (message-item count unchanged, not a new appended item).
        3. Verify the model label and a loading/streaming indicator appear
           (Stop control occupies the composer's send-slot, PLUS the full
           RotatingMessages/Thought-accordion/model-chip sequence — reused
           ELITEA-2181/2182 contract).
        4. Verify the user's previous message is byte-identical before and
           after.
        5. Wait for the new response to complete; verify it is non-empty
           coherent content (the response is the oracle — not asserted
           against a hand-written string, AFS § Fidelity Declaration) AND
           that it genuinely differs from the pre-regenerate text (HARD
           assertion — the case's own headline claim; a rare coincidental
           identical LLM repeat is accepted ordinary flakiness, not a
           reason to demote this to a log line).
        6. Verify Regenerate and the full action-icon row reappear.
        """
        chat = ChatPage(page)
        console_issues = []
        page_errors = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_issues.append(msg)

        page.on("console", _on_console)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        with allure.step("Setup — navigate to the fresh conversation; send one message"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            user_index = chat.get_message_count()
            ai_index = self._send_and_wait(chat, "Hi there")

        with allure.step("Step 1 — Hover the completed response; verify Regenerate is visible"):
            ai_message = chat.messages_container.nth(ai_index)
            user_message = chat.messages_container.nth(user_index)
            ai_message.scroll_into_view_if_needed()
            ai_message.hover()
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 2 — Click Regenerate; verify the previous response is "
            "replaced IN PLACE (message-item count unchanged)"
        ):
            pre_click_count = chat.get_message_count()
            pre_click_body = chat._extract_message_body(ai_message)
            pre_click_user_body = chat._extract_message_body(user_message)
            chat.regenerate_action_button.click()

        with allure.step(
            "Step 3 — Verify the model label and loading/streaming "
            "indicator appear on the regenerating response (Stop control "
            "occupies the composer's send-slot; RotatingMessages/Thought-"
            "accordion/model-chip sequence, reused ELITEA-2181 contract — "
            "AFS Coverage Map row 3)"
        ):
            expect(chat.stop_generation_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_loading_placeholder).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_thought_accordion).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(chat.answer_model_chip).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            "Step 4 — Verify the user's previous message is unchanged "
            "while regeneration is in flight"
        ):
            assert chat._extract_message_body(user_message) == pre_click_user_body, (
                "User's previous message should remain unchanged during regeneration"
            )

        with allure.step(
            "Step 5 — Wait for the new response to complete; verify it is "
            "non-empty coherent content and the message list did not grow"
        ):
            self._wait_for_regeneration_complete(chat)
            post_click_count = chat.get_message_count()
            assert post_click_count == pre_click_count, (
                "Regenerate should replace the message IN PLACE, not append "
                f"a new one — count was {pre_click_count} before, "
                f"{post_click_count} after"
            )
            post_click_body = chat._extract_message_body(ai_message)
            assert post_click_body and post_click_body.strip(), (
                "Regenerated response should be non-empty coherent content, "
                f"got: {post_click_body!r}"
            )
            # Hard assertion (fix round 1, review finding): this is
            # ELITEA-2185's own HEADLINE claim ("Clicking Regenerate
            # Generates a New Response") — demoting it to a `logger.warning`
            # means a Regenerate that no-ops and returns cached/identical
            # text passes this test green, which is exactly the No Defect
            # Masking Rule's forbidden "demote expect() to log.info" shape.
            # See `.agents/testing.md` § Fidelity policy ("the response is
            # the oracle, not a payload you wrote") — the invariant this
            # case exists to prove must be asserted, not merely observed.
            # A rare coincidental identical LLM repeat on a short, open-ended
            # prompt ("Hi there") is accepted ordinary test flakiness, not
            # masking — a failure here is signal to investigate, never
            # something to silently swallow.
            assert post_click_body != pre_click_body, (
                "Regenerated response text is identical to the pre-regenerate "
                "text — Regenerate should generate a genuinely NEW LLM "
                f"completion, not resurface cached/identical content: {post_click_body!r}"
            )

        with allure.step(
            "Step 6 — Verify the user's message is STILL unchanged after "
            "completion, and Regenerate + the full action row reappear"
        ):
            assert chat._extract_message_body(user_message) == pre_click_user_body, (
                "User's previous message should remain unchanged after regeneration completes"
            )
            ai_message.scroll_into_view_if_needed()
            ai_message.hover()
            expect(chat.regenerate_action_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(ai_message.locator(chat.READ_OUT_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(ai_message.locator(chat.COPY_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )
            expect(ai_message.locator(chat.DELETE_ACTION_BUTTON)).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step("Side-channel check — no unexpected console/JS errors"):
            assert not console_issues and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_issues]!r}; "
                f"page errors: {page_errors!r}"
            )
