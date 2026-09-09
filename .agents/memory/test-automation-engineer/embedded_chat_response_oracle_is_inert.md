---
name: Embedded-chat "agent responded" assertions are inert by default
description: wait_for_chat_response() warns instead of raising and get_last_chat_response_text() falls back to raw <li> text — so `response_text != ""` passes on the loading placeholder
type: feedback
aliases: [inert response assertion, wait_for_chat_response does not raise, skill-test-last-response oracle, embedded chat agent responded, wait_for_embedded_chat_response, pipeline run completion wait]
tags: [area/chat, type/masking-trap]
created: 2026-08-27
updated: 2026-09-09
---

## The trap

In `AgentDetailPage` (agent-detail embedded chat), the obvious "the agent
answered" assertion **cannot fail**:

```python
detail_page.wait_for_chat_response(initial_count=n, timeout=AI_RESPONSE_TIMEOUT)
response_text = detail_page.get_last_chat_response_text()
assert response_text != ""          # INERT — always true
```

Two independent fallbacks combine into a vacuous green:

1. `wait_for_chat_response()` **never raises**. On timeout it logs
   `WARNING … Clear chat button not visible` / does not stabilize, and returns
   normally.
2. `get_last_chat_response_text()` falls back to the **raw last-`<li>` text**
   when `skill-test-last-response` is absent (`ApplicationAnswer.jsx` sets that
   testid only on a real answer). The answer **placeholder is its own
   `chat-message-item`**, so the read returns e.g.
   `'…toMessageless than a minute agoWaking the agent…'` — non-empty.

Net effect: a run where the send registered but **the agent never answered goes
GREEN**. Measured live on ELITEA-1886 (issue #1812, 2026-08-27).

## The honest oracle

Assert the **answer element itself**, which only a real answer renders:

```python
expect(detail_page.skill_test_last_response.first).to_be_visible(
    timeout=UI_ELEMENT_TIMEOUT          # after wait_for_chat_response has already waited
)
response_text = detail_page.get_last_chat_response_text()
assert response_text != ""
```

And read the **user's own** message at a FIXED index, never `.last` — the
placeholder can already occupy the next slot:
`detail_page._embedded_chat_messages().nth(initial_count).text_content()`.
Match by **containment**, not equality: the `<li>` also carries header metadata
(`'TBTest Bottoelitea-1886-…less than a minute agoHow do I create a new agent?'`).
`AgentDetailPage` has **no** indexed body-text reader — `ChatPage.get_message_text_at()`
has no counterpart there.

## Confirmed sibling — `PipelineDetailPage.wait_for_embedded_chat_response()`

Same inertness, **different mechanism and oracle** (ELITEA-2448 / #2076,
2026-09-09). It logs `WARNING Embedded chat response did not stabilise within
timeout` and returns. On a pipeline that emits no chat answer it burns its whole
budget every run: its `[aria-label="Delete"]` wait takes **all remaining budget**
inside a bare `try/except: pass` and that action bar never appears; and the
placeholder **rotates every 2.0 s**, defeating `stable_duration_ms=3000`.
Measured: Step 4 = **90.36/90.38 s ≡ the full 90 000 ms timeout** on runs that
*passed*, so the CI red surfaced as a misleading "element(s) not found".
After the repair: **33.66 s**.

The honest oracle is **not** a chat element (there is no answer) — it is the run's
own state: `wait_for_run_node_on_canvas()` (STARTED) then
`wait_for_run_details_status("Completed")` off
`pipeline-run-details-status-badge`'s `data-status`, which updates in place while
the panel is open. ⚠️ Open the panel **once** (the MUI Dialog then intercepts a
second run-node click); `pipeline-run-node-label` means STARTED, not finished.
**Do not "fix" the helper — 20 caller files depend on it.** Detail:
`test-specs/pipelines/_surface.md` § "Pipeline EXECUTION waits".

## Where else to look

The same two-fallback shape exists on the `ChatPage` side. Any spec asserting
"an AI response arrived" via a non-empty **text read** rather than the
**answer-element testid** is suspect. Grep: `get_last_chat_response_text()`
followed by a `!= ""` / truthiness assertion with no
`skill_test_last_response` wait.

Related: [[chat_send_button_force_click_race]] — same case, same Step 8; a
silent no-op send plus this inert oracle is how a fully-broken step still
reported green locally.
