---
name: Correcting an AFS call-site/component claim does NOT also fix _surface.md — check both
description: When Phase 2 exploration flips a claim the AFS made (wrong component, wrong call site, wrong selector), also grep test-specs/<feature>/_surface.md for the same pre-correction claim — it's a separate file, drifts independently, and the reviewer will catch it as its own round
type: feedback
---

## The situation (ELITEA-2369, PR #1235, fix round 2)

During implementation I found the AFS named the wrong call site for a shared
component's new testid prop (`ChatConversationStarters.jsx` instead of the
actual-flow `NewConversationView.jsx`). I corrected the AFS's Concrete
Handles row + Known Defects section + the test docstring — all three now
agreed on the right call site.

What I did NOT do: check whether `test-specs/agent-hub/_surface.md` (the
exploration digest I — the same implementer session — had no reason to
re-open, since it's analyst-authored) made the same pre-correction claim.
It did: "wire only `ChatConversationStarters.jsx`'s call site for now …
`NewConversationView.jsx`'s own call site is a DIFFERENT case's job" — the
exact backwards guidance. Reviewer caught it in a SEPARATE re-review round,
costing a full round-trip that fixing it alongside the AFS correction would
have avoided.

## The reusable check

Whenever a Phase 2 exploration flips an AFS's claimed component/call-site/
selector, before considering the correction done:

```bash
grep -n "<the wrong claim's key term>" test-specs/<feature>/_surface.md
```

If it hits, append an attributed `[CORRECTION, ...]` note in the same PR/
commit that fixes the AFS — don't rewrite the analyst's original bullet in
place (Hard Rule 11: `_surface.md` is analyst-authored; implementer may only
append attributed facts). Do this proactively during the SAME dispatch that
made the original correction, not only after a reviewer flags it as a
separate blocker.

See also qa-engineer's `surface_digest_can_stay_wrong_after_afs_call_site_correction.md`
(same incident, reviewer side) — `_surface.md` is a 4th triangulation
artifact the reviewer contract doesn't name (TMS case / AFS / implementation
are the three it does), so it's easy for both sides to forget it exists.

## Recurred (ELITEA-2450, PR #1269, fix round 1 → round 2)

Same failure shape, different trigger: round 1 fixed a stale ALL-CAPS
"TIMELINE STEP"/"STATES" paraphrase (presented as confirmed-live fact) in
FOUR spots inside the AFS, but not in `test-specs/pipelines/_surface.md`'s
"Body composition" bullet — added in the SAME original commit, carrying the
identical wrong paraphrase, never re-grepped. Reviewer caught it as a
separate round-2 blocker. **Generalization: it isn't only call-site/
component corrections that need the `_surface.md` grep — ANY confirmed-live
text/fact correction the AFS receives should trigger the same
`grep -n "<the stale quoted text>" test-specs/<feature>/_surface.md` check,
same dispatch, before calling the fix done.** A `_surface.md` section and
its sibling AFS are very likely to share the same drift when both were
authored in one original commit.
