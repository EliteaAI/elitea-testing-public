---
name: Runtime-composed testid mechanism can itself be testids-only, not just the call site
description: Extends the dynamic-testid promotability lessons — sometimes the SHARED COMPOSITION MECHANISM (not just the per-case call-site fragment) is still pending promotion to main
type: feedback
---

Prior memory (`dynamic_testid_promotability_grep.md`, `dynamic_testid_promotability_needs_3hop_trace.md`)
established: for a runtime-composed testid (e.g. `${id}-menu-button`), check the
composition MECHANISM and the per-case call-site fragment SEPARATELY, because a bare
literal grep on the fully-composed string always false-negatives.

ELITEA-1817 (#252, PR #668) surfaced a variant those entries didn't cover: it is NOT
always true that "the mechanism is on main, only the call site is testids-only." For
`artifacts-bucket-retention-measure-select-combobox`, BOTH were still testids-only:

- The root testid (`artifacts-bucket-retention-measure-select`, `CreateBucket.jsx`) —
  testids-only, from ELITEA-1808's `0c8e0d63`.
- The `-combobox` suffix-derivation mechanism itself (`SingleSelect.jsx`'s
  `SelectDisplayProps={dataTestId ? { 'data-testid': \`${dataTestId}-combobox\` } : undefined}`)
  — ALSO testids-only, traced via `git log origin/main..origin/automation/testids -- <file>`
  to `EliteaAI/EliteaUI@301d131c`, a completely unrelated feature (ELITEA-1955, a pipeline
  MCP-node toolkit-select combobox) that happened to touch the same shared component.

Compare: the `${testId}-menuitem` mechanism in `DotMenu.jsx` for
`bucket-menu-delete-menuitem` WAS already on main (only the per-item `key` fragment in
`BucketItem.jsx` was testids-only) — so both shapes can occur in the same delivery.

**Practical rule:** for every runtime-composed testid, check FOUR things independently,
not two: (1) call-site value/fragment on main, (2) call-site value/fragment on
automation/testids, (3) composition mechanism on main, (4) composition mechanism on
automation/testids. Don't assume the mechanism is settled just because it "looks like"
established shared-component code — grep it fresh every time, and when it's absent from
main, resolve ITS OWN commit via `git log origin/main..origin/automation/testids -- <file>`
too (it may belong to an entirely different, unrelated case).
