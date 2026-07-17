---
name: Support Assistant conversation pagination truncation defect
description: GET /api/v2/support_assistant/conversation/{uuid} returns only the oldest 100 message_groups once a conversation exceeds that count (no pagination params, no most-recent fallback) — filed as GH#607; relevant to ANY future Support Assistant history/restore/session case
type: feedback
---

Confirmed live on `http://localhost:5173/chat` (2026-07-17, ELITEA-1799 analysis).
Filed: https://github.com/EliteaAI/elitea-testing-public/issues/607 (Major).

## The defect

`GET /api/v2/support_assistant/conversation/{uuid}` — the endpoint the
Support Assistant widget calls both to render the default/active
conversation on page load AND to restore a conversation selected from
Chat History — returns a top-level `message_groups_count` field that is
always correct, but the `message_groups` array itself is capped at
**100 items**, and those 100 are the chronologically **oldest** ones, not
the most recent. The request carries no `limit`/`offset`/cursor params at
all, so there is no way for the widget to reach the tail.

Confirmed via direct response-body inspection: conversation `id 503`
(`uuid f53736b2-e54a-4c95-926d-318cc4483181`, this test account's primary,
long-lived Support Assistant conversation) reports
`message_groups_count: 218` but its `message_groups` array has exactly
100 entries, with the last one dated 5 days stale relative to the test
run. `GET /api/v2/support_assistant/conversations/` (the LIST endpoint)
correctly reports `updated_at` advancing and `message_groups_count`
incrementing on every new send — the data really is persisted
server-side, just unreachable via the singular-conversation fetch once
past ~100 groups.

Reproduced 2 independent ways in the same session: (a) Chat History →
select the affected entry, (b) a plain full-page reload with zero
history interaction at all. Both return byte-identical stale content —
this rules out "History selection is buggy" as the cause; it's the
conversation-fetch path itself (shared by both).

**Scoped to large conversations only** — a brand-new conversation (e.g.
one lazily created via `POST /api/v2/support_assistant/conversations/`
after clicking "New Chat" and then sending a message) renders correctly
end-to-end since it's well under the ~100-group cap. Don't conflate this
with a general "Support Assistant is broken" — messaging, New Chat, and
History selection UI all work; only the conversation-content fetch for
conversations >100 groups is affected.

## Why this matters for future cases

This test account's shared dev-token Support Assistant conversation
(id 503, "HI Chat") has been growing across every qa-engineer session
that opens the widget without clicking New Chat first (218 groups as of
2026-07-17, purely from repeated QA runs since 2026-06-29). **Any future
case that inspects this conversation's rendered message content** (not
just "does the widget open" / "does a message send") will hit this same
truncation and may misdiagnose it as a fresh finding, or worse, may
misdiagnose an unrelated *new* defect as "just the known 100-cap issue"
without re-verifying. Before either:
- re-file this as a duplicate — search for GH#607 first;
- write off a discrepancy as "probably the pagination bug" — confirm via
  the same response-body inspection technique (compare
  `message_groups_count` to `len(message_groups)` and check the last
  entry's `created_at`) rather than assuming.

## Also useful: New Chat's actual mechanics (not itself a defect)

Discovered while isolating this: clicking "New Chat" fires **zero**
network requests — it's a pure client-side view reset (clears the
rendered message array, shows a canned welcome message). The backend
conversation a "New Chat" session will eventually belong to is created
**lazily**, only on the first message send after the click
(`POST /api/v2/support_assistant/conversations/` → `201 Created` with a
fresh `uuid`). If you need to test "does New Chat create a genuinely new
session," you must send a message first — checking immediately after the
click will show no new conversation exists yet, which is correct/expected
behavior, not a bug.
