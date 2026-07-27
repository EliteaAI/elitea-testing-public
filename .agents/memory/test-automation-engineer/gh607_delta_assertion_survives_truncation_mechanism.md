---
name: GH#607 delta-assertion survives truncation — verified mechanism
description: Why a relative-delta message-count assertion (final_count > restored_count) is safe from GH#607's fetch-time truncation, verified by direct reproduction against the real truncated conversation rather than assumed from the assertion shape
type: feedback
---

## Context

ELITEA-1800's AFS (`test-specs/support-assistant/lextend_history-restore-and-continue-messaging_ELITEA-1800.md`)
had a "GH#607 relevance check" section with two review-flagged defects (PR #626
fix-only round, 2026-07-18): the truncation direction was stated backwards, and
the reasoning self-contradicted on session size (claimed the restored session is
bounded to "the test's own ~1-2 message pairs" while the next bullet documented
the same session holding 20+ accumulated messages across runs — it's actually a
shared, cross-run, ever-growing dev-token conversation with no cleanup).

## GH#607's actual direction (confirmed twice, independently)

`GET /api/v2/support_assistant/conversation/{uuid}` returns exactly the
**oldest** 100 message groups (`created_at` ascending) and silently drops
everything after that — it drops the **newest** groups, keeps the **oldest**
~100. Confirmed via a direct `curl`/fetch against the exact conversation the
issue documents (id 503, uuid `f53736b2-...`, 218 total groups): the returned
array's last item was dated ~8 days stale relative to the probe date. Any text
claiming GH#607 "keeps the newest ~100" has the direction backwards.

## The generalizable pattern

A **relative-delta count assertion** (`final_count > restored_count`, not an
absolute floor or exact-content match) on a **live, append-only DOM** survives
a fetch-time-only truncation bug — but ONLY if the mutating action performed
between the two counts (here: sending a follow-up message) never re-triggers
the truncating fetch. That's a specific, checkable fact about the
implementation, not a property you get for free from the assertion being
delta-shaped. Verify it live; don't assume it.

**How it was verified for ELITEA-1800** (not asserted): read
`SupportAssistantPage`'s implementation — `get_assistant_message_count()` is a
pure DOM count (`.elitea-assistant-message-wrapper--assistant`);
`select_history_session()` is the ONLY method that fires the truncating
`GET .../conversation/{uuid}`; `send_message()`/`wait_for_response()` only poll
the DOM, never re-fetch. Then reproduced directly against the real
GH#607-truncated conversation (id 503) via `playwright-cli`: force-restored it
through the widget's own history panel, observed the DOM render exactly 100
truncated wrappers with `restored_count` (assistant wrappers) = 47 — GH#607
reproducing live — sent a real follow-up message through the UI, confirmed via
`playwright-cli requests` that zero additional GETs to the conversation
endpoint fired during/after the send, and watched the count settle at
`final_count` = 48. `48 > 47` held under genuine, currently-reproducing
truncation.

## Reusable technique for finding a "shared/growing" test conversation to probe

`GET /api/v2/support_assistant/conversations/` (list endpoint, paginated) —
sort the `items` by `message_groups_count` descending to find any conversation
near/over a suspected truncation threshold, independent of what the widget's
history panel shows by default (which is usually only the most-recent page by
`updated_at`, not sorted by size). The exact GH#607 conversation (id 503) was
still present and reachable this way months after the original bug report.

## Caveat (stated explicitly in the AFS, don't drop it if this pattern is reused)

This safety is an implementation detail of the current widget (append-on-send,
never re-fetch), verified today — not an inherent property of count-based
assertions in general. If the widget is ever changed to re-fetch the full
conversation after every send, a re-fetch would reapply the same fixed
oldest-100 window and could leave `final_count` unchanged, breaking this exact
assertion. Re-verify if that changes.

(from ELITEA-1800, PR #626 fix-only round)
