---
name: HITL sensitive-action resume drops the turn on BOTH Authorize and Block
description: Block looks healthy only because non-execution is also what a dead turn produces — the response step is the real oracle
type: feedback
aliases: [1834, 1835, sensitive action block, hitl resume dropped, phantom card]
tags: [area/chat, area/hitl, type/product-defect]
created: 2026-08-27
updated: 2026-08-27
---

## The fact (live-verified 2026-08-27, two runs, ELITEA-2213)

The Sensitive Action Authorization resume is dropped on the **Block** path exactly as
#1834 documents for Authorize:

- the card closes correctly (~0.1-4 s), then **reappears at ~2-6 s with live, enabled
  buttons** and persists until a page reload (#1835's shape, far faster than its ~90 s)
- **no assistant response ever arrives** — the answer body stays empty (observed 230 s);
  after a reload the turn persists as `"Thought for 3 secs"` with no body
- no console error, no failed request, no error frame — it dies silently
- a `beforeunload` guard stays armed: the app still believes a generation is in flight
- the decision is never committed as a tool outcome, so **the next user message
  re-triggers the identical card** instead of being answered

## The trap this closes

On Block, the case's primary observable ("the tool does not execute") is **satisfied by
the failure** — a dead turn deletes nothing either. So a Block test that asserts only
file-presence reads GREEN on a completely broken flow. The assertion that actually
separates "blocked" from "died" is the **response** step.

Corollary for ordering: never put the case's primary observable behind
`wait_for_message_content_stable()` — that wait times out at 60 s here, so the
observable is never evaluated at all.

Related: [[hitl_tool_chip_is_call_attempt_not_execution]]
