---
name: confirmed_live_is_not_on_main_provenance_check
description: "confirmed live" (dev server = automation/testids) is NOT proof a testid is on EliteaUI main — verify each separately in the PROVENANCE column
type: feedback
---

Caught reviewing ELITEA-2049 (`test_pipeline_three_dot_menu_actions.py`, PR #1338).
The AFS's Concrete Handles table labelled `fork_menuitem`'s testid
(`pipeline-actions-fork-menuitem`) as `on-main ✓ — confirmed live`, and the
implementer's PR body / memory log repeated it as one of "5 pre-existing,
on-main testids". Both are wrong.

**Why it's wrong:** localhost:5173 serves `EliteaAI/EliteaUI`'s
`automation/testids` branch, NOT `main` (`.agents/architecture.md`). "Confirmed
live" only proves a testid exists on `automation/testids` — it says nothing
about `main`. Verification:

```bash
cd ../EliteaUI && git fetch origin
git grep -n "FORK_MENU_ITEM_KEY_BY_ENTITY" origin/main -- src/     # no hits
git grep -n "FORK_MENU_ITEM_KEY_BY_ENTITY" origin/automation/testids -- src/
# origin/automation/testids:src/components/Fork/ForkEntityButton.jsx:23:const FORK_MENU_ITEM_KEY_BY_ENTITY = {
git log --oneline origin/main..origin/automation/testids -- src/components/Fork/ForkEntityButton.jsx
# 5dbc7530 test: [EL-1893] fix state-conditional testid and shared-component testid scoping
# 61328689 test: [EL-1893] add data-testids for Fork wizard elements
```

`fork_menuitem`'s testid was added by a *prior* case (EL-1893, 2026-07-16) and
is still sitting on `automation/testids`, unpromoted — the exact same state as
this PR's own `pin_to_top_menuitem`, just not labelled that way.

**The check, every time a handle is marked provenance `on-main`:** don't infer
it from "the dev server showed it" — `git grep` the literal key/testid string
against `origin/main` specifically (after a fresh `git fetch origin`), same as
the closure-record verification in `.agents/workflow.md`. A testid can be
real, correct, and fully confirmed live, and still not be on `main` — those are
independent facts and the PROVENANCE column exists precisely to keep them
separate (`.agents/role-overrides.md` § Analyst slot).

Non-blocking finding (test itself is correct and green; the miscategorization
only misleads the eventual closure record, which the orchestrator
independently re-verifies anyway per workflow.md) — flagged so the AFS/PR-body
wording gets corrected rather than propagating into memory as "5 pre-existing
on-main".
