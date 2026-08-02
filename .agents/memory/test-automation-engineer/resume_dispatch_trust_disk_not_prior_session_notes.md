---
name: Resume dispatch — trust disk, not the prior session's notes
description: A force-ended session's own "work completed" note can describe work that never got committed and didn't survive a later checkout in the shared tree — grep for it before reusing it.
type: feedback
---

## What happened (2026-08-02, ELITEA-2181, batch wave-01)

A prior implementer session was force-ended mid-verification (StructuredOutput
deadline cut it off during a legitimately slow 34-54s live pytest run). Its
own final note claimed the page-object changes (`chat_page.py` — 4 new
`LocatorDescriptor` fields + a `wait_for_message_body_growth()` method) were
"present on disk, on branch `tests/ELITEA-2181-chat-streaming-response`". The
orchestrator's own recovery grep had already found them absent and said so in
the dispatch — but the note's confident wording ("Work completed this
session (all present on disk, ...)") was worth double-checking anyway before
assuming the *rest* of the note was equally reliable.

Confirmed via a fresh `grep` that zero of the 7 new symbols existed in
`chat_page.py` on the branch — the AFS commit and the testid push (both real
git artifacts) had survived; the page-object edits (never committed) had not,
because an uncommitted edit in a shared working tree does not survive a later
`git checkout` by another agent/session using the same clone.

## The fix

On any resume dispatch ("a prior session did X, verify/finish it"):

1. Don't take the prior session's own completion claim as ground truth for
   *anything uncommitted*. Committed git artifacts (a commit SHA, a pushed
   branch, a merged PR) are real; "I wrote the method" or "the fields are
   there" is not, until you `grep` for it yourself in the actual current
   working tree.
2. The orchestrator's dispatch prompt in this case already did this
   groundwork (ran the grep, named exactly which symbols were missing) —
   when it has, trust that recovery grep over the failed session's own
   narrative, and treat the prior note as a *spec* (what to rebuild, named
   fields/testids/behavior) rather than a status report.
3. Re-verify anything the note asserts about EXTERNAL state (e.g. "testids
   are already live") independently too — in this case `git grep` against
   `origin/automation/testids` in the EliteaUI sibling clone confirmed the 6
   testids really were live, in the exact JSX shape described, before wiring
   any `LocatorDescriptor` to them.

## Why this matters beyond this one case

A force-ended session is not an unusual failure mode on this team (deadline
cutoffs during legitimately slow live-pytest waits are expected, not rare) —
whoever resumes such a unit should default to "verify, then trust", not
"trust because it's oddly specific and confident-sounding".
