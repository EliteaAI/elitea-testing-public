---
name: Absence assertions must scope their side channel
description: Page-wide "zero POSTs in a window" proofs false-fail on unrelated background traffic — scope by URL/event
type: feedback
aliases: [zero POST assertion, no-send proof, absence assertion, side channel capture]
tags: [area/ui-tests, type/flakiness]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

A "nothing was sent" proof is often written as a page-level capture plus
`assert posts == []` over a settle window. That asserts *no POST anywhere on
the page*, not *no send* — any unrelated background request in the window
(analytics, token refresh, a socket.io polling fallback, a lazy chunk POST)
turns it red for a reason that has nothing to do with the case.

Seen on ELITEA-2418 (`tests/ui/support_assistant/test_support_assistant_empty_message.py`,
Steps 4 / 5b): correct observable, over-broad capture.

## The shape that holds

- Filter the captured channel by what the product would actually emit for a
  send — a URL substring for HTTP, an event name for a socket frame — and
  assert that filtered list is empty. ELITEA-2418 already does this correctly
  for WebSocket (`predict` frame filter); the POST half was left unfiltered.
- On Elitea, **sending is a Socket.IO `predict` frame, not a POST**
  (`elitea_assistant` `chat.hook.ts:152`). The socket-frame assertion is the
  load-bearing one; a POST assertion is a bonus and should not be the thing
  that decides the verdict.

## Related

Absence has no positive condition to wait on, so these proofs need a settle
window — see the suite's `NO_SEND_SETTLE_MS` pattern and the canon tension
between `.agents/conventions.md` ("no `waitForTimeout`") and the 146 existing
in-suite usages.
