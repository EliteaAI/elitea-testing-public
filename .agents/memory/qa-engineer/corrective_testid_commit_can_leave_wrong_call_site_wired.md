---
name: A corrective testid commit can leave the original wrong-call-site wiring in place
description: "Corrected call site" claims in an AFS/test docstring aren't proof — grep the live automation/testids state, don't trust the narrative
type: feedback
---

## The situation (ELITEA-2369, PR #1235)

The AFS's Concrete Handles table originally told the implementer to wire a
new `testId` prop for the shared `EllipsisTextWithTooltip` at
`ChatConversationStarters.jsx`'s call site. Implementer commit `a0bc4305`
did exactly that. Live exploration then showed this case's actual flow
renders through a DIFFERENT call site, `NewConversationView.jsx` — commit
`5694aa81` added the testid there too, titled "wire ... at the correct call
site." The AFS/test-file docstring were both updated to say
"`ChatConversationStarters.jsx`'s call site remains unwired — out of scope."

That claim was false. The corrective commit only ADDED the right wiring; it
never REMOVED the wrong one from the first commit. `git grep` on
`origin/automation/testids` showed `testId="chat-conversation-starter-tile"`
present at BOTH call sites — an orphan testid on an element this test's
executed code path never touches, exactly the scope violation
`.agents/role-overrides.md`'s locator policy exists to catch, and a
documentation claim that didn't match reality.

## The reusable check

When an AFS/test docstring narrates "the AFS originally named the wrong
call site, corrected to X, Y stays unwired" — that's a claim about a
DIFFERENT repo's branch state (`EliteaAI/EliteaUI` `automation/testids`),
not something the diff under review can verify by itself. Don't take the
narrative on faith:

```bash
cd ../EliteaUI && git fetch origin
git grep -n "<the testid>" origin/automation/testids -- src/
```

If it appears at more call sites than the AFS claims, the "corrected" story
is incomplete — the fix added the right wiring but didn't clean up the
wrong one. This is a `CHANGES_REQUESTED`, not a nit: it's simultaneously an
orphan-testid scope violation (corrupts the presence-based coverage metric)
and a false claim in the artifact the next reader trusts.
