---
name: wait_for_chat_response header text false-stable
description: wait_for_chat_response() could lock onto static header/thought-accordion text as "stable" before the real Answer body rendered
type: feedback
---

## Symptom

`AgentDetailPage.wait_for_chat_response()` (and, by extension, any caller
that reads the response right after it returns) intermittently returned a
premature/wrong content read. The give-away string pattern in the captured
"stable" text: `...toMessage less than a minute ago Thought for less than a
second...` — that is header metadata + the "Thought for Ns" accordion, not
the answer body. Two specs hit it: `test_agent_run_history_select_past_run.py
::test_select_past_run_loads_chat_messages` and
`test_agent_management.py::TestAgentExecution::
test_agent_executes_with_name_description_instructions_only` — both use
`llm_settings.reasoning_effort: "low"`, which makes the header + thought
accordion go static almost immediately, well before the answer streams.

## Root cause

`wait_for_chat_response()`'s stability loop preferred
`skill_test_last_response` (the `skill-test-last-response` testid,
`ApplicationAnswer.jsx`'s `Answer` element on the last message) but **fell
back to raw `messages.last.text_content()`** whenever that testid hadn't
rendered yet — pulling in the header (participant name, "to"/"Message"
reply-to `Typography` pair, `CreatedTimeInfo` relative time) and the
"Thought for Ns" accordion, both of which live OUTSIDE the `Answer` element
in the JSX. A `len(current) < 100 and "toMessage" in current` guard tried to
filter this out but was length-gated, so a sufficiently long
agent-name/header string bypassed it — the loop then saw the header text go
unchanged for `stable_duration_ms` and returned believing the answer had
rendered.

`get_last_chat_message()` / `get_last_chat_response_text()` have the
identical-shaped fallback, but only matter once `wait_for_chat_response()`
has already (mis)declared readiness — fixing the wait closes them too, no
separate change needed.

## Fix (2026-08-07, batch-stabilize round 1)

In the stability loop: when `skill_test_last_response.count() == 0` (or its
`text_content()` is falsy), treat it as **not ready** — reset the stability
window and keep polling — instead of falling back to the raw `<li>` text.
Dropped the now-dead `toMessage` length guard (with the fallback gone, that
testid's own text can never contain header/loading noise — confirmed in
`ApplicationAnswer.jsx`: the header block and `RotatingMessages` loading
placeholder are both siblings of, not children of, the `Answer` element that
carries `skill-test-last-response`).

## Where this bites

Any test using `wait_for_chat_response()` (11 callers across
`tests/ui/agents|artifacts|admin|skills/`) with a **fast/low-effort agent**
(`reasoning_effort: "low"`/`"none"`, or any run where the header settles
before the answer streams) is the shape most likely to have hit this. If a
chat-response assertion reads suspiciously like header/metadata text instead
of the actual answer, or a test intermittently reads a stale/short "response"
that doesn't match what streamed, check this method first before adding a
sleep or blaming the product.
