---
name: AFS single-handle claim may hide a sibling untested value
description: An AFS Concrete-Handles row claiming one testid "reads X + Y" (e.g. tokens + percentage) can be describing two separate DOM nodes — verify against JSX before trusting the row as one assertable read.
type: feedback
---

## What happened (ELITEA-2216, PR #1604)

The AFS's Concrete Handles table (`context-budget-tokens` row) said: *"Confirmed live in
the DISABLED state: `context_budget_tokens_display` reads `"0 / 6 400 tokens"` +
`"0%"`"* — phrased as if one handle/read covers both the token fraction AND the
percentage. Likely the analyst read both values visually/via accessibility snapshot in
the same live glance, not via one DOM node.

Checked the actual EliteaUI source (`ContextBudgetProgress.jsx` for the sidebar panel,
`ContextBudgetStats.jsx` for the "Edit context settings" modal): in BOTH places the
`data-testid` (`context-budget-tokens` / `context-modal-stat-tokens`) sits on a
`<Typography>` containing ONLY the tokens fraction (`{tokensDisplay} tokens` /
`{item.value}`). The percentage (`{utilizationPercentage}%` / `{item.suffix}`) is a
**separate sibling `<Typography>` with NO testid at all** — in either location.

The implementer, trusting the AFS's phrasing, never asserted the percentage anywhere —
even though the case's own text (and the AFS's own Coverage Map, marking the rows
"asserted — confirmed live exactly as written") names "0%" as an explicit expected
value at three separate steps (4, 6, 7). The gap survived because nothing in the AFS
or the diff literally claimed a nonexistent testid — it just implied one shared read
where there were two DOM nodes, one of which has no handle at all.

## Reviewer takeaway

When an AFS Concrete-Handles row (or a Coverage Map "asserted" cell) claims a single
handle/read yields **two distinct displayed values** (a value + an adjacent unit/percent/
suffix), don't take the claim at face value even if "confirmed live" — check the actual
render (JSX for UI, response shape for API) to see whether it's really one text node or
two. Two nodes means the second one needs ITS OWN testid and ITS OWN assertion; a
missing one is real under-coverage even though the diff contains no fabrication and no
locator-ladder violation to grep for.
