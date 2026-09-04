"""Conversation starter chips appear in the embedded chat panel and are
clickable (ELITEA-1886).

Adds two conversation starters to a dedicated agent via the "Chat starters"
accordion (agent form), Saves, reloads for a pristine embedded-chat mount,
verifies both starter chips render before any message is sent, clicks one
chip (pre-fill only — no auto-send, chip row disappears immediately), then
explicitly sends via `chat-send-button` and verifies the agent responds.

Step 8 — repair history (issue #1812). Two rounds.

**Round 1 (2026-08-27, PR #1851, merged `ac6b4dbdc`)**, after GHA run
32931571484 on dev.elitea.ai failed `assert 0 > 0`. It stopped forcing the
Send click (Playwright now waits for actionability), gated it on
`to_be_enabled()`, wrapped it in
`page.expect_response(_is_send_response)` asserting the conversation POST's
201, and replaced Step 8's inert observables — `assert response_text != ""`
could not fail (`wait_for_chat_response()` only WARNs on timeout, and
`get_last_chat_response_text()` falls back to the raw last-`<li>` text when
`skill-test-last-response` is absent, so the answer *placeholder* satisfied
it), so the test now also asserts the user message at index `initial_count`
carries the exact starter text and waits for the `skill-test-last-response`
element itself, which `ApplicationAnswer.jsx` renders only on a real answer.
Those three observables were already specified in the AFS (§ Test Steps 8) and
had been dropped during the original implementation — implementation-vs-AFS
drift, so neither the AFS nor the TMS case needed amending.

**Round 2 (this change).** A week of DEV runs showed round 1's *diagnostic*
half working and its *robustness* half not: run 33066098636 (08-27) PASSED,
run 33149201954 (08-28) FAILED on all three attempts at the `expect_response`
wait, run 33488691004 (09-01) PASSED. The 08-28 failure screenshots (all three
attempts byte-identical) show the composer still holding the starter text, a
completely empty chat list, and Send rendered enabled — the send genuinely
never fired, and round 1's oracle correctly said so in ~15s by naming the
missing POST instead of vacuously burning the 60s AI timeout.

**The mechanism — and it is NOT the stale closure round 1's docstring claimed;
that was a guess and it was wrong.** Send is gated twice: by the DOM
(`disabled={disabledSend || !question}`, `SendButton.jsx:79`) and by the
handler itself (`if (question.trim() && !disabledSend)`, `UserInput.jsx:238`).
React delivers a synthetic handler from the CURRENT fiber props, not from the
render the browser gated on — so a commit landing between the browser
dispatching the click and React delivering it hands `sendQuestion()` a
`disabledSend` that is now `true`, and it early-returns silently: no exception,
no console error, no request. `disabledSend` is `ChatBox.jsx:2747`'s nine-term
`isInputDisabled` disjunction, several of whose terms are network-bound and
settle late on a deployed env. `to_be_enabled()` therefore NARROWS that window
but cannot close it — the deciding gate is on the handler side, after
Playwright has stopped looking. The click here was dispatched, not blocked:
`conftest.py`'s 10s context default would have raised an actionability error
naming the button, and this raised at 15s on the *response*. Filed as product
bug #2011.

So Step 8 now **bounded-retries the CLICK** (`SEND_ATTEMPTS`) — the shape canon
already prescribes for the analogous HITL trigger-side flake
(`.agents/testing.md` § Known issues: "a bounded retry of the trigger
message... not a longer panel timeout"). What keeps that a retry-of-an-action
rather than masking is its discriminator: it retries ONLY when it can prove
nothing was sent, and re-raises immediately otherwise.

**Why the discriminator is the REQUEST and not the composer-clearing
invariant.** The obvious reading of the source does not hold for this
component. `UserInput.jsx`'s `sendQuestion()` does clear the composer
synchronously before calling `onSend` — but only `if (clearInputAfterSend)`,
and `ChatBox.jsx` passes **`clearInputAfterSubmit={false}`** to the composer's
`<NewChatInput>` (`ChatBox.jsx:2950`, the same JSX element as
`onSend={onSendMessage}` at 2898). Here the composer is reset by the CALLER
instead, at `ChatBox.jsx:1174` — *after* `await onSend(...)` (1059) and
`await uploadAttachments(...)` (1085), and only on the success path. A
populated composer is therefore a LAGGING signal, equally consistent with
"nothing was sent" and with "a send is in flight whose POST has not returned
yet"; retrying on it alone could fire a second send.

`sendQuestion()`'s early return, by contrast, happens *before* any network
call. So if the conversation POST was ever ISSUED, the send registered —
whether or not its response arrived. A `page.on("request", ...)` listener
records exactly that. The retry fires only when the request was never issued
AND the composer is still populated: strictly narrower than either signal
alone, and if either one says the send registered, the failure re-raises
unchanged. A send that actually happened is never retried.

The response-side 4xx/5xx catcher also now records `"<status> <url>"` rather
than a bare status, so a future failure there names a resource instead of
reading `[404]` — the same URL-capture gap `.agents/testing.md` § Unconfirmed
spent three entries closing on the console side.

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
from playwright.sync_api import Page, Request, Response, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
SAVE_RESPONSE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000

#: Bounded retries of the Step 8 Send CLICK (product bug #2011 — the handler
#: reads fresher props than the DOM the browser gated on, so a click the DOM
#: permitted can still early-return with nothing sent). Retried only when
#: nothing was provably sent; see the module docstring.
SEND_ATTEMPTS = 3

STARTER_1 = "How do I create a new agent?"
STARTER_2 = "What toolkits are available?"


def _is_save_response(response: Response) -> bool:
    """Check if response is an agent save PUT request."""
    return (
        "application/prompt_lib" in response.url
        and response.request.method == "PUT"
    )


def _is_send_response(response: Response) -> bool:
    """Check if response is the embedded-chat Send POST.

    Sending from the embedded chat creates the conversation via
    ``POST /api/v2/elitea_core/conversations/prompt_lib/{project_id}``
    (AFS § Network Behavior; live URL observed as
    ``.../conversations/prompt_lib/399``). Matched on the path segment only,
    so the predicate is project-id agnostic and holds on any environment.
    """
    return (
        "/conversations/prompt_lib/" in response.url
        and response.request.method == "POST"
    )


def _is_send_request(request: Request) -> bool:
    """The same match as :func:`_is_send_response`, on the REQUEST side.

    ``UserInput.jsx``'s ``sendQuestion()`` early-returns *before* any network
    call, so the mere ISSUING of this POST proves the Send click registered —
    independently of whether its response ever arrived. That is what makes it a
    sound discriminator for Step 8's bounded click retry, where the composer's
    contents are only a lagging signal (module docstring).
    """
    return "/conversations/prompt_lib/" in request.url and request.method == "POST"


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


# The response-side counterpart of the console filter above, for the same known
# defect (#1971 / #554). Deliberately keyed on the URL and matched with
# ``str.endswith``, mirroring ``utils.console_errors.exclude_known_defect_urls``
# — that helper itself is not reachable from here: it lives on `automation/base`
# and is not yet on `main`, which this branch targets.
#
# NEVER keyed on the status code: an "any 4xx" filter would swallow the next
# genuine one, which is masking (`.agents/testing.md` § Unconfirmed says so
# explicitly). And ``endswith`` rather than ``in``, because #1971's entire
# signature is the MISSING trailing project-id segment — a well-formed
# ".../toolkits/prompt_lib/399" still surfaces as a real, unexpected failure.
def _is_known_1971_toolkits_request(entry: str) -> bool:
    return entry.endswith("/elitea_core/toolkits/prompt_lib/")


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
        a real agent response.

        Step 8's Send is a plain (non-force) click gated on the send POST's own
        201, and "the agent responded" is proven by the
        `skill-test-last-response` answer element — not by a non-empty text read
        that the loading placeholder also satisfies. See the module docstring
        for the full rationale (issue #1812).
        """
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
        # Capture the URL alongside the status. A bare ``[404]`` names no
        # resource, so a failure here is untriageable — exactly the URL-capture
        # gap `.agents/testing.md` § Unconfirmed spent three entries closing on
        # the console side (`utils/console_errors.format_console_message`).
        failed_responses: list[str] = []
        page.on(
            "response",
            lambda resp: failed_responses.append(f"{resp.status} {resp.url}")
            if resp.status >= 400
            else None,
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
                # Deliberately a plain, unforced click — and, since round 2,
                # a retried one.
                # The starter chip never TYPES: `ChatBox.jsx`'s
                # `onSendConversationStarter` populates the composer
                # programmatically through an imperative ref
                # (`chatInput.current.setValue(starter)` → `UserInput.jsx`). Send
                # is then gated twice: the DOM
                # `disabled={disabledSend || !question}` (`SendButton.jsx:79`) and
                # the handler's own `if (question.trim() && !disabledSend)`
                # (`UserInput.jsx:238`), where `disabledSend` ← `isInputDisabled`
                # is `ChatBox.jsx:2747`'s NINE-term disjunction carrying several
                # network-bound terms.
                #
                # Correction to round 1's comment here, which blamed a stale
                # closure: React delivers the synthetic handler from the CURRENT
                # fiber props, so it is a FRESHER `disabledSend` — not a staler one
                # — that early-returns on a click the DOM had already permitted.
                # `to_be_enabled()` narrows that window; it cannot close it,
                # because the deciding gate runs after Playwright stops looking.
                # Product bug #2011; module docstring has the full account.
                #
                # Same trigger pattern as the two sibling starter-flow specs
                # (test_agent_hub_create_conversation_via_starter.py,
                # test_chat_agent_starters_add_remove.py), which are exposed to
                # this race too — canon card #1849 owns that sweep, not this file.
                # Round 2 (issue #1812, product bug #2011): bounded retry of the
                # CLICK. Each attempt re-arms the send's OWN response oracle, so a
                # no-op still fails in ~15s naming the POST that never fired rather
                # than vacuously burning 60s on a message count that never moved.
                #
                # This listener is what makes the retry honest. It records the
                # conversation POST at ISSUE time; `sendQuestion()` early-returns
                # before any network call, so a recorded request proves the send
                # registered even if its response never arrived.
                send_requests: list[str] = []
                page.on(
                    "request",
                    lambda req: send_requests.append(req.url) if _is_send_request(req) else None,
                )

                send_response = None
                for attempt in range(SEND_ATTEMPTS):
                    expect(detail_page.chat_send_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)
                    try:
                        with page.expect_response(
                            _is_send_response, timeout=SAVE_RESPONSE_TIMEOUT
                        ) as send_info:
                            detail_page.chat_send_button.click()
                        send_response = send_info.value
                        break
                    except PlaywrightTimeoutError as err:
                        # Retry ONLY when nothing was provably sent. Two independent
                        # proofs that it WAS sent, either of which re-raises at once:
                        #
                        #  1. the conversation POST was issued (authoritative — it is
                        #     downstream of `sendQuestion()`'s guard);
                        #  2. the composer is empty (`ChatBox.jsx:1174` resets it only
                        #     on the send path).
                        #
                        # Signal 2 alone is NOT sufficient here: this component passes
                        # `clearInputAfterSubmit={false}` (`ChatBox.jsx:2950`), so the
                        # reset happens after `await onSend(...)` — a populated
                        # composer is equally consistent with an in-flight send, and
                        # retrying on it alone could fire a second one. See the module
                        # docstring.
                        #
                        # ⚠️ REUSING THIS PATTERN ELSEWHERE: signal 1 is only valid
                        # while the send is expected to CREATE the conversation.
                        # `needsConversationCreation` (`ChatBox.jsx:1052`) is
                        # `!activeConversation?.uuid && isAgentsPage`, so a send into
                        # an ALREADY-EXISTING conversation issues no POST at all and
                        # the request signal would be silent — a false "nothing was
                        # sent". Unreachable here (Steps 5/6/7 assert a message count
                        # of 0 three times, and any earlier attempt that had created
                        # a conversation would itself have recorded the request and
                        # re-raised), but a continuing-conversation flow inherits a
                        # false oracle if it copies this shape unchanged.
                        #
                        # Each branch raises its OWN message: three semantically
                        # different outcomes must be distinguishable from the pytest
                        # tail alone, without allure or screenshots. Chained with
                        # `from err` so the originating timeout stays in the
                        # traceback — nothing is swallowed and nothing goes green.
                        # (Round 1's failure cost a week of forensics precisely
                        # because the tail said nothing; a retry that collapses the
                        # three outcomes into one byte-identical traceback would
                        # re-create that cost.)
                        if send_requests:
                            raise AssertionError(
                                f"Send REGISTERED (conversation POST issued: {send_requests}) "
                                f"but no matching response arrived within "
                                f"{SAVE_RESPONSE_TIMEOUT}ms on attempt {attempt}. "
                                "NOT product bug #2011 — the click landed; investigate "
                                "the backend/response."
                            ) from err
                        composer = detail_page.chat_message_input.input_value()
                        if composer == "":
                            raise AssertionError(
                                f"No conversation POST was issued on attempt {attempt}, "
                                "yet the composer is EMPTY — neither 'sent' nor "
                                "'not sent'. Unexpected state, not #2011."
                            ) from err
                        if attempt == SEND_ATTEMPTS - 1:
                            raise AssertionError(
                                f"Send click no-opped on all {SEND_ATTEMPTS} attempts: "
                                "no conversation POST ever issued, composer still holds "
                                f"{composer!r}. Product bug #2011."
                            ) from err

                # Unreachable by construction (the loop breaks or re-raises) — kept
                # as an explicit type guard rather than an implicit AttributeError.
                assert send_response is not None, "Send loop exited without a response"
                assert send_response.status == 201, (
                    "POST .../conversations/prompt_lib/... should return 201 on Send, "
                    f"got {send_response.status}"
                )

                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                assert detail_page.get_chat_message_count() > initial_count, (
                    "Message count should increase after sending the pre-filled starter"
                )

                # The USER's own message carries the clicked starter's exact text.
                # Read at the FIXED index `initial_count` rather than `.last` — a
                # transient AI placeholder ("Waking the agent…") can already
                # occupy the next slot (same reason ChatPage.get_message_text_at()
                # exists for the sibling /chat/{id} flow). `_embedded_chat_messages()`
                # is the page object's own testid-scoped collection
                # (`chat-message-list` > `chat-message-item`); AgentDetailPage has
                # no indexed body-text reader and this repair is scoped to the spec
                # file, so the raw <li> text is matched by CONTAINMENT — the item
                # also renders header metadata (participant name, timestamp)
                # alongside the body.
                user_message_text = (
                    detail_page._embedded_chat_messages().nth(initial_count).text_content() or ""
                )
                assert STARTER_1 in user_message_text, (
                    f"User message at index {initial_count} should carry the clicked "
                    f"starter text {STARTER_1!r}, got: {user_message_text!r}"
                )

                # The agent ACTUALLY answered. ApplicationAnswer.jsx sets
                # `skill-test-last-response` only on a real answer element, so this
                # cannot be satisfied by the loading placeholder (which is its own
                # `chat-message-item`). Without it the trailing `response_text != ""`
                # assertion was INERT: `wait_for_chat_response()` only WARNs on
                # timeout, and `get_last_chat_response_text()` falls back to the raw
                # last-<li> text when the testid is absent — so a run where the send
                # registered but the agent never answered read
                # "…toMessageless than a minute agoWaking the agent…" and passed.
                # `.last` (not `.first`) to agree with
                # `get_last_chat_response_text()`'s own `.last` read. Behaviour is
                # identical today — ApplicationAnswer.jsx's
                # `isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'`
                # ternary means only ONE element ever carries this testid — but
                # `.last` is the semantically correct form for a "last response"
                # oracle and stays correct if that ever changes.
                expect(detail_page.skill_test_last_response.last).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                # Retained as belt-and-braces, NOT as the oracle: the assertion
                # above is what actually proves the agent answered. On its own this
                # line is near-inert (see the module docstring) — it now guards only
                # the residual case of the answer element rendering visible but
                # empty, which the `shouldRenderAnswerBlock` gate (`!!answer`) makes
                # unlikely. Kept rather than deleted because it costs nothing and
                # narrows the failure description when it does fire.
                response_text = detail_page.get_last_chat_response_text()
                assert response_text != "", "Agent response should be non-empty"

            unexpected_console_errors = [
                m for m in console_errors if not _is_known_554_toolkits_404(m)
            ]
            assert not unexpected_console_errors, (
                "Unexpected console errors during the run: "
                f"{[m.text for m in unexpected_console_errors]}"
            )
            # Known defect: #1971 (a regression of the closed #554) — EliteaUI's
            # `toolkits.js` `toolkitTypes` endpoint races `useSelectedProjectId()`
            # and builds the URL with the project-id segment MISSING
            # (".../elitea_core/toolkits/prompt_lib/"), which the backend answers
            # 4xx. The console-side listener in this same spec already excludes it
            # (`_is_known_554_toolkits_404`) and the response-side listener sees the
            # identical request, so filtering one axis and not the other is
            # incoherent.
            #
            # The two filters are deliberately NOT identical, and this is not an
            # oversight: `_is_known_554_toolkits_404` requires `"404" in msg.text`
            # AND the URL, because a ConsoleMessage carries no status field to key
            # on. This one is URL-only, mirroring `exclude_known_defect_urls()` —
            # the canon helper keys on the URL and never on the status code, so a
            # 500 from that same malformed request is excluded here but would still
            # surface on the console axis. Narrower is the console filter; the
            # canon shape is this one.
            unexpected_failed_responses = [
                r for r in failed_responses if not _is_known_1971_toolkits_request(r)
            ]
            assert not unexpected_failed_responses, (
                f"Unexpected 4xx/5xx responses: {unexpected_failed_responses}"
            )
        finally:
            console_errors.stop()
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
