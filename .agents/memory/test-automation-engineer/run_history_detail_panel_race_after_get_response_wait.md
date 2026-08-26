---
name: Run History detail panel race after GET-response wait
description: select_run_history_item() awaits the conversation GET response but not React committing the message list — get_run_history_chat_messages_text() can transiently read ""
type: feedback
---

`AgentDetailPage.select_run_history_item()` (ELITEA-1877) waits for
`page.expect_response()` on `GET /elitea_core/conversation/prompt_lib/...`
before returning — that only proves the network round trip finished, not that
`RunHistoryChat.jsx`'s `ChatMessageList` has actually re-rendered with the new
conversation's messages. `get_run_history_chat_messages_text()` used to read
`_embedded_chat_messages()` immediately, with no wait — a transient "" read
was reproducible (2/4 live runs, ELITEA-1876 implementation, 2026-08-06/07).

Fix (additive, backward compatible — only 1 caller at the time):
`get_run_history_chat_messages_text(timeout=10000)` now does
`messages.first.wait_for(state="visible", timeout=timeout)` before reading,
falling back to logging a warning + returning whatever is present (preserves
the "" contract for a genuinely empty case).

Separately, `test_select_past_run_loads_chat_messages`'s own Step 2 (embedded
chat "last message contains Message B" assertion) is ALSO independently
flaky — AI-response timing, unrelated cause, same test. The AFS
(`lextend_..._ELITEA-1876.md`) already flagged both signatures from the
analyst's own 2-run exploration; worth a dedicated stability look at
ELITEA-1877 before/at the next hardening gate — the Step 2 flake is NOT fixed
by the wait above.
