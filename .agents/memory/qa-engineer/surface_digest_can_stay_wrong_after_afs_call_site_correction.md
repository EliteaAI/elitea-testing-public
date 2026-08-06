---
name: A surface digest (_surface.md) can keep the WRONG call-site advice after the AFS/test corrects it
description: When Phase 2 exploration flips an AFS's claimed call site, also grep _surface.md for the same claim — it's a 4th artifact the reviewer triangle doesn't name, and it drifts silently
type: feedback
---

## The situation (ELITEA-2369, PR #1235, re-review)

The AFS's Concrete Handles table originally told the implementer to wire a
new `testId` prop for the shared `EllipsisTextWithTooltip` at
`ChatConversationStarters.jsx`'s call site. Live exploration during
implementation showed the case's ACTUAL flow renders through a different
component, `NewConversationView.jsx` — the implementer re-wired there,
removed nothing extra (a *separate* bug, already caught and fixed in fix
round 1: an orphan copy of the testid left on the original wrong call site),
and amended the AFS's Concrete Handles row + Known Defects section + the
test docstring to all say "wired at `NewConversationView.jsx`'s call site;
`ChatConversationStarters.jsx` stays unwired." All three of those now agree.

But `test-specs/agent-hub/_surface.md` — the exploration digest the analyst
wrote and commits alongside the AFS (`test-case-analysis` § "Exploration
digest") — still said the opposite: "wire only `ChatConversationStarters.jsx`'s
call site for now … `NewConversationView.jsx`'s own call site is a DIFFERENT
case's job." Nobody had gone back and corrected it after the call-site flip,
because the digest isn't one of the three artifacts the reviewer contract
names to triangulate (TMS case / AFS / implementation) — it's easy to read
the AFS's Known Defects amendment, confirm it's internally consistent, and
never open `_surface.md` at all.

This is a real hazard, not a paperwork nit: `_surface.md` is exactly the file
a FUTURE analyst on this same surface reads first, on the promise it's a
verified handle cache. Backwards call-site advice there would reproduce the
exact mistake this case's implementer already made and already paid a
review round to fix.

## The reusable check

Whenever a PR narrates "the AFS named the wrong call site/component,
corrected to X" (or any other AFS Known-Defects/Concrete-Handles
correction), also grep the feature's `_surface.md` for the same claim:

```bash
grep -n "<the corrected thing>" test-specs/<feature>/_surface.md
```

If it still states the pre-correction version, that's `CHANGES_REQUESTED` —
the digest is a 4th artifact carrying the same class of claim as the AFS,
and it drifts independently of whatever the AFS/test-docstring narrative
says was swept.
