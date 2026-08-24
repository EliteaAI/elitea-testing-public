---
name: Chat detail pane — the input echo defeats list-level assertions
description: Asserting on chat-message-list/-item verifies the INPUT, never the output; use the answer-content testid
type: feedback
aliases: [chat-message-item, chat-message-list, skill-test-last-response, chat-answer-content, run history detail, input echo, tool call echo]
tags: [area/chat, area/toolkits, type/assertion-strength]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

Every chat-style detail pane in Elitea (Run History for agents / pipelines /
toolkits+MCPs, the Test Settings panel) renders BOTH the request and the
response as `[data-testid="chat-message-item"]` inside one
`[data-testid="chat-message-list"]` — `UserMessage.jsx:127` and
`ApplicationAnswer.jsx:578` both emit the same literal testid.

For a **tool run** the request message is
`Calling '<tool>' with parameters: { "repoName": "facebook/react" }`
(`toolkits.helpers.js:281`). It therefore already contains the tool name and
every parameter value — i.e. exactly the strings a test is most likely to
assert on.

Consequence: `expect(message_list).to_contain_text(<tool>)`,
`…to_contain_text(<param value>)` and `to_have_count(2)` are **all satisfied
by the input alone**, and `count == 2` counts *input + error* identically to
*input + output*. The output goes completely unverified while the test reads
green. Caught in PR #1728 review (ELITEA-1940).

## The fix

Only `ApplicationAnswer.jsx:710` emits an answer-content testid:
`isLastMessage ? 'skill-test-last-response' : 'chat-answer-content'`. In a
run-history detail pane the answer IS the last message, so
`skill-test-last-response` is what renders — but match **both**, since the
value depends on position, not on the page:

```python
DETAIL_ANSWER_CONTENT_SELECTOR = (
    '[data-testid="skill-test-last-response"], [data-testid="chat-answer-content"]'
)
# scoped sub-selector off the list container — compliant with the testid-only
# locator policy (both alternatives are [data-testid= literals)
self.detail_message_list.locator(self.DETAIL_ANSWER_CONTENT_SELECTOR)
```

Then assert input and output through **separate handles**, and add the
locator self-check `expect(answer).not_to_contain_text("Calling '<tool>' with
parameters")` — if the answer handle ever collapses back onto the input, that
fires instead of every output assertion silently becoming unfalsifiable.

Verified live 2026-08-24 (toolkit 2140 run history): the answer node carries
`skill-test-last-response` + `chat-copy-button` and reads
`Available pages for AsyncFuncAI/deepwiki-open: 1 …`; the input node carries
only `chat-message-sender-avatar` / `chat-message-sender-name`.

Related: [[wait_for_tool_result_returns_on_error_too]] ·
[[toolkit_run_history_row_is_a_conversation]]
