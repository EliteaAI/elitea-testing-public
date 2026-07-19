---
name: AFS Concrete Handles table can both omit real deps and over-include unused ones
description: tracing the merged test's actual page-object call chain for promotability can find BOTH testids the AFS's handles table never listed (implicit waits inside navigate()/wait_for_page_load()) AND testids the AFS did list but the implementation never touches (an AFS-documented cleanup-path alternative the implementer didn't take) — check both directions, don't just add rows for gaps
type: feedback
---

## What happened (ELITEA-1901, issue #181, PR #629)

Tracing the merged test's own page-object call chain (not just re-verifying
the AFS's "Concrete Handles" table row by row) turned up two distinct kinds
of mismatch in the same case:

1. **Omission** — `agents-page-header` and `agent-information-section` are
   real runtime dependencies (waited on inside
   `AgentsListPage.navigate()`/`AgentDetailPage.navigate()`'s
   `wait_for_page_load()`), but the AFS's handles table never named them —
   it was written pre-implementation and only listed handles the case's
   literal steps touch directly, not the page-objects' own internal wait
   targets.
2. **Over-inclusion** — the AFS's Cleanup section documented TWO options
   ("delete via API" OR "if API cleanup isn't wired, via UI: three-dot menu
   → Delete"), and listed the UI-path testids
   (`agent-actions-menu-button`/`delete-agent-menuitem`/
   `delete-confirm-name-input`/`delete-confirm-button`) in the Concrete
   Handles table as if they were used. The implementer took the API path.
   Those 4 testids are never touched by the merged code at all — carrying
   them into the promotability table would have repeated the #139-audit
   fabrication class (a table row for a testid the code never calls).

## The check

Don't just tick the AFS's own table against `main`/`testids` — independently
derive the dependency set from the merged diff's actual call chain (every
page-object method the test calls, one hop into each), THEN diff that
derived set against the AFS's table in both directions:
- **AFS lists it, call chain doesn't touch it** → exclude (AFS documented an
  alternative path that wasn't the one actually shipped).
- **Call chain touches it, AFS doesn't list it** → include (usually an
  implicit wait-helper dependency the AFS pass didn't think to enumerate).

Only the derived set — not the AFS's table verbatim — belongs in the
promotability check.

## Recurrence (ELITEA-1868, issue #236, PR #657)

Same omission shape again: the AFS's Concrete Handles table (14 rows) never
listed `empty-state-title`, but the merged `ToolkitsListPage.empty_state_title`
field IS asserted by the test (step 13's secondary check). Caught by deriving
the dependency set from `grep -nE 'testid\s*=\s*"'` across the new page
objects + `import`-following into `ArtifactsPage` for indirect deps, then
diffing against the AFS table — the same procedure this entry already
prescribes. Ground truth happened to be benign here too (testid existed on
`automation/testids`, just needed the fresh main/testids check like every
other row), but the closure record would have silently shipped a 15-row
table instead of 16 without the independent re-derivation. Reinforces: do
this trace on every case, not just ones where a mismatch is suspected.
