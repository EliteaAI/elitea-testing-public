---
name: Testid draft-PR-to-main flow suspended 2026-07-16
description: Per-case testids no longer get a draft PR to EliteaUI main — they stop at automation/testids, a human batch-promotes out of band; Ready no longer requires a draft PR, only committed+pushed to automation/testids; a reused testid still absent from main is not a Ready-blocker under this policy
type: project
---

## What changed

As of 2026-07-16, operator-suspended (see `EliteaUI`/`elitea-testing-public`'s
`.agents/_reverted/RESTORE-testid-draft-pr-flow.md` for the exact revert
recipe if this ever comes back):

- **Before:** each case's new testid commits got cherry-picked from
  `automation/testids` onto a fresh `testids/<case>-<slug>` branch (cut from
  `origin/main`, in a worktree) and opened as a **draft PR to
  `EliteaAI/EliteaUI` `main`**. Closure records tracked "promotability" as
  "is there an open draft PR for this case's testids."
- **After:** testids are born on `automation/testids` and **stop there**.
  Agents commit + push to `automation/testids` — nothing downstream. A human
  cherry-picks `automation/testids` → `main` in a batch, out of band. Agents
  **never** open an `EliteaUI` `main` PR anymore.

## What's unchanged

- Testids are still committed AND pushed to `automation/testids` (not left
  local).
- `sync-base-branches`'s `git merge origin/main` into `automation/testids`
  is untouched.
- The merge-gate expectation that a test PR's testids are on
  `origin/automation/testids` before the test PR merges stays.

## What this means for `Ready` and closure records

`Ready` no longer requires a draft PR at all — the dispatch's own definition
of done spells this out explicitly now ("no EliteaUI main PR — suspended
2026-07-16 ... a human promotes"). A closure record's promotability table
should still be verified fresh (per-testid `main` vs `automation/testids`
row, don't trust "already exists" at face value — the
`promotability_must_cover_every_dependency_not_just_this_prs.md` lesson still
applies to REUSED testids), but a `NO` on `main` for a reused/shared testid
is now just informational, not a blocker — note it plainly, don't hold the
card at `In Progress`/`Blocked` waiting on it.

First applied on issue #87 (ELITEA-1883): 3 of 5 reused testids
(`agent-variables-section`, `agent-variable-row-{name}`,
`agent-variable-input-{name}`, all owned by ELITEA-1884/#76) were absent from
`main`, present only on `automation/testids` — reported in the closure record
as an informational row, card still went to `Ready`.
