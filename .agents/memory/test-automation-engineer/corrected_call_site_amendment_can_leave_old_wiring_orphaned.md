---
name: A "corrected the call site" AFS amendment can leave the original wrong wiring in place
description: When Phase 2 exploration shows the AFS named the wrong component/call site for a new testid, re-wiring the RIGHT one doesn't remove the WRONG one — check both, or ship an orphan
type: feedback
---

## The situation (ELITEA-2369, PR #1235, fix round 1)

Implementing ELITEA-2369, the AFS's Concrete Handles table originally told me
to wire a new `testId` prop for the shared `EllipsisTextWithTooltip` at
`ChatConversationStarters.jsx`'s call site. I did that (commit `a0bc4305`).
Live exploration then showed the case's ACTUAL flow renders through a
DIFFERENT call site, `NewConversationView.jsx` — so I added the testid
there too (commit `5694aa81`) and amended the AFS + test docstring to say
"the testId prop is wired at `NewConversationView.jsx`'s call site instead
… `ChatConversationStarters.jsx`'s own call site remains unwired."

That claim was false the moment I wrote it: I had only ADDED the correct
wiring, never REMOVED the incorrect one from the first commit. Both call
sites carried the identical testid on `automation/testids`. Fresh-session
review caught it via `git fetch origin` + `git grep <testid>
origin/automation/testids -- src/` showing two hits instead of one — an
orphan out-of-scope testid (corrupts the presence-based coverage metric,
`.agents/testing.md`) PLUS a false documentation claim in the artifact the
next reader trusts.

## The reusable check

When Phase 2 exploration reveals the AFS named the wrong component/call
site for a NEW testid you're about to add:

1. Wire the testid at the correct call site (as normal).
2. **Also check whether an earlier commit in this same dispatch already
   wired it at the WRONG call site** — `git log --oneline -- <wrong-file>`
   or just re-read your own diff so far. If so, REMOVE that wiring; don't
   just add the right one and assume the wrong one aged out on its own.
3. Before claiming "X remains unwired" in the AFS/docstring, verify it with
   `git grep <testid> origin/automation/testids -- src/` — the same
   ground-truth check a reviewer will run. A claim about a call site is a
   claim about live branch state, not something the local diff proves by
   itself.

"Corrected the call site" is an ADD operation in your head, but if the
original wrong wiring was already a real commit, closing the loop requires
a REMOVE too. This is the same shape as any other correction: fixing where
something SHOULD be doesn't undo where it already IS.
