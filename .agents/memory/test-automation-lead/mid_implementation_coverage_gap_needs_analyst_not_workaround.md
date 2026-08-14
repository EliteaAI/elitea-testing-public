---
name: Mid-implementation coverage gap needs analyst resume, not implementer workaround
description: When Phase-2 implementer exploration finds the AFS's own test data can't exercise the case's core assertion (not just a selector/timing issue), treat it as a scope/coverage change — resume the analyst to pick better data, don't let the implementer silently substitute an edge-case assertion for the real one
type: feedback
---

## What happened (ELITEA-1739, issue #29)

An AFS was corrected once already (search activates on Enter/send-icon, not
live-typing — issue #44 was case-text drift, not a bug) and gated
`ready-for-automation`. The implementer picked it up and, in Phase 2
exploration, found the AFS's own partial-search term (`"Co"`, 2 chars) could
never activate the search at all — the product enforces a 3-char minimum.
The implementer correctly refused to assert the stale claim (reverse-masking
guard), but its first fix asserted the min-length-guard toast instead — which
means the case's actual point (partial search narrows to the right subset)
was now completely untested, replaced by an unrelated edge case.

## Why this needed the analyst, not just an implementer fix

The Phase 2 rule is explicit: a **scope/coverage** change (the case needs
different assertions/test data) returns `needs-analyst-rerun`; only
**technique** changes (different wait strategy, different tool) are the
implementer's call. Swapping what's being asserted — "partial match works"
becomes "query-too-short shows a toast" — is a coverage change, not a
technique change, even though it's framed as "just fixing what the AFS got
wrong." Picking the *replacement* test data (which skill names, which query
string) is a test-data-selection judgment call — exactly the kind of thing
the analyst is scoped to do, and exactly the kind of thing an implementer
under schedule pressure will otherwise solve by asserting whatever the
product actually does at hand, not what the case asked for.

## What resuming the analyst caught that a quick implementer fix would have missed

Given the narrow task ("find test data that clears the 3-char minimum and
still narrows correctly"), the analyst didn't just pick any 3-char substring
— it exhaustively checked all three skill-name pairs, found none shared one,
and while testing a rename candidate discovered a SECOND, previously
undocumented product behav0r: the grid search matches on **description
text**, not just the name field. Naively picking a "close enough" term
would have shipped a test that was accidentally correct locally but fragile
against unrelated fixture data. This is the kind of validation depth a
scope-preserving analyst pass buys that a plug-the-gap implementer fix
usually doesn't.

## The general rule

When an implementer's Phase 2 (or later) exploration finds that the AFS's
prescribed test data can't exercise the case's core assertion — not a
selector, not a wait, but the actual DATA the case's pass/fail criteria
depend on — treat it exactly like the first scope-change discovery: resume
the analyst (narrow, additive dispatch — same technique as
`resuming_subagents_for_narrow_fixups.md`), don't let the implementer
self-serve a replacement assertion, even a well-reasoned and correctly
un-masked one. A red flag for this pattern: the implementer's own Run
Report or PR description explicitly recommends "an analyst rerun ... if the
original intent needs restoring" — that sentence is the implementer
correctly recognizing the boundary and you should act on it, not merge
around it.
