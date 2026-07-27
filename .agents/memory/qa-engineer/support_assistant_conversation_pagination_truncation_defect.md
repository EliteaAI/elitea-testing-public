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

## UPDATE 2026-07-18 — even having this entry didn't prevent a reversed-direction claim

PR #626/ELITEA-1800 reviewer-slot pass (fresh session, adversarial) caught the
ELITEA-1800 AFS's own "GH#607 relevance check" section
(`test-specs/support-assistant/lextend_history-restore-and-continue-messaging_ELITEA-1800.md:139-168`)
stating the *opposite* truncation direction from this entry and from GH#607's
own text: "GH#607's truncation failure mode (dropping the *oldest* groups,
**keeping the newest ~100**)" — reversed; the defect keeps the oldest 100
and hides the newest/recent activity, exactly as documented above. The same
AFS section is also internally self-contradictory: one bullet claims the
restored session "can only ever accumulate the ~1–2 message pairs **the
test itself sends**" (implying growth is bounded per-test-run), while the
very next bullet in the same section documents that same session holding 20
messages "accumulated across multiple prior automated runs" against the
shared dev-token conversation — i.e. NOT bounded to one test run at all, and
growing exactly the way this entry's "Why this matters" section already
warned about.

**Lesson**: having an accurate memory entry on file is not sufficient —
re-derive defect-mechanics claims from the primary source (`gh issue view
607`) every time they're used in a new relevance argument, don't reason from
recollection/pattern-match even when a correct prior write-up exists
verbatim two paragraphs earlier in the same document (line 142 of that AFS
correctly restates "oldest 100", then line 164 reverses it 22 lines later).
The practical conclusion (Step 15's `final_count > restored_count` assertion
is likely still safe) probably survives on a *different*, unstated argument
— `get_assistant_message_count()` counts rendered DOM wrappers, and a
follow-up send likely appends a wrapper client-side regardless of what the
initial restore-fetch truncated to — but the AFS's own stated reasoning does
not establish that, and "structurally insulated... unlike ELITEA-1799" is
not a safe permanent claim given the conversation's unbounded, no-cleanup,
cross-run growth documented right in this entry.

## UPDATE 2026-07-18 (round 2) — fixed, and independently reproduced live against the real truncated conversation

Implementer's fix-only pass (`4ac282fb`) corrected both the direction and the
self-contradiction, and added a *new, verified* mechanism explaining why
Step 15 survives truncation: `select_history_session()`
(`automation/pages/support_assistant_page.py:362-399`) is the only page-object
method whose click causes the app to re-fire
`GET /api/v2/support_assistant/conversation/{uuid}`; `send_message()`
(L194-221) and `wait_for_response()` (L223-267) never touch that endpoint —
they only fill/click the input and poll DOM state via `wait_for_function`.
So `restored_count` and `final_count` are always read from the same
(possibly truncated) DOM render; the delta assertion doesn't care whether
that render was truncated.

I (reviewer-slot, round 2, separate fresh session) independently reproduced
this live rather than trusting the implementer's claim or the code-read
alone: opened `/chat` on localhost, History → selected "HI Chat"
(conversation id 503, `uuid f53736b2-e54a-4c95-926d-318cc4483181` — the same
conversation this entry documents), confirmed truncation live
(`assistantCount=47`, `totalCount=100`), captured one
`GET .../conversation/f53736b2-...` firing on selection. Sent a follow-up
message and watched network requests through response completion — **zero**
additional GET to that endpoint fired; `assistantCount` settled at 48
(48 > 47 held). Numbers matched the implementer's own reproduction exactly.

**Reusable fact for future Support Assistant history/restore cases in this
module**: the truncating fetch only fires on `select_history_session()`
(session switch), never on send/response-wait. Any assertion shaped as
"count after follow-up > count after restore" is safe from GH#607 regardless
of how large the shared dev-token conversation grows, as long as the
follow-up path stays DOM-append-only (re-verify this specific mechanism if
the widget's package (`@eliteaai/elitea-assistant`) is ever upgraded — it's
an implementation detail, not a documented contract).
