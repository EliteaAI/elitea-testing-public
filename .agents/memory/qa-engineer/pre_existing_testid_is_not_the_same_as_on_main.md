---
name: "Pre-existing" testid is not the same as "on main"
description: An AFS row can read on-main ✓ for a testid another case added to automation/testids only — always run the TWO-ref grep, never infer main from "it already existed".
type: feedback
aliases: [provenance on-main false row, testid pre-existing, automation/testids only, closure record promotability]
tags: [area/review, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

`automation/testids` accumulates every testid the team ever added, so a testid an
EARLIER case introduced is genuinely "already there" for anyone exploring on
localhost — the dev server serves that branch. An analyst who checks only "did I add
this one?" writes `on-main ✓` for it, and the false row flows straight into the
closure record's promotability claim (the #19 / #35-#37 failure class).

Worked example — ELITEA-1844 (PR #1639): `delete-confirm-title-icon` was listed
`on-main ✓`. Fresh two-ref grep after `git fetch origin`:

```
delete-confirm-title-icon      main:no   testids:YES
```

It was added by EliteaAI/EliteaUI@7b359d32 for a *different* case (EL-2193) and has
never been cherry-picked to `main`. Two of the case's three pending testids were
declared; the third read as "pre-existing" and silently became "promotable".

## The check

For EVERY handle row (not just the ones this case added), run both refs:

```bash
cd ../EliteaUI && git fetch origin
git grep -qi -- "$t" origin/main -- src/ ; git grep -qi -- "$t" origin/automation/testids -- src/
```

Composed/prop-wired testids need the caller-side check too — see
[[provenance_grep_needs_case_insensitive]]. And when a testid rides a prop
(`titleIconTestId`, `closeButtonTestId`), diff the component between the two refs
(`git diff origin/main origin/automation/testids -- <file>`) rather than grepping:
that diff shows all of a case's additions at once, which is how this one surfaced.

Related: [[provenance_grep_needs_case_insensitive]] · [[agent_hub_catalog_testid_provenance_was_wrong_in_prior_afs]]
