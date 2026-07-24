---
name: EliteaUI's own pre-commit hook (husky+lint-staged) reformats files on every testid commit
description: A testid-only edit to EliteaUI JSX can pick up cosmetic import-reorder / line-wrap diffs from the repo's own eslint --fix + prettier --write pre-commit hook — this is NOT implementer scope creep and is not fixable by manually reverting (the hook reformats it right back and blocks an now-empty commit).
type: feedback
---

## What happened (ELITEA-1880 review Nit, fix round R1)

A reviewer flagged that the `add-data-testid` commit for ELITEA-1880
(`EliteaAI/EliteaUI@d364790b`) touched `LLMSettingsDialog.jsx` with two lines
that look like unrelated scope creep beyond the testid-only edit:

1. An import reorder (`shallowEqual` moved above `Button, Modal`).
2. `hasChanges`'s `useMemo` collapsed from 3 lines to 1.

## Root cause, verified empirically

`EliteaUI` has a `husky` pre-commit hook running `lint-staged` ->
`eslint --fix` + `prettier --write` on every staged `.js`/`.jsx` file. I
manually reverted both lines to their pre-testid-commit shape, staged, and
committed — the hook silently reformatted the file BACK to the exact same
"scope creep" shape mid-commit, and since the net diff after reformatting
was now empty, `lint-staged` aborted with "Prevented an empty git commit!".

This means: **any commit that touches this file will always carry these two
cosmetic diffs** (or the equivalent formatter output for whatever the file's
current content is) — there is no way to make a testid-only commit to this
file that's ALSO prettier/eslint-clean, because the file's committed-on-main
state itself isn't in the format the hooks would produce.

## What to do

- **Don't try to manually "clean up" formatter-driven diffs in EliteaUI
  commits** — it's a wasted round-trip (confirmed above) and the hook wins.
- **When a reviewer flags this class of "unrelated diff" Nit**, verify by
  diffing the touched file against `origin/main` for JUST the lines the
  testid change needs (`data-testid=`, `closeButtonTestId=`, `testId=`,
  `containerTestId=` props) — if the ONLY semantic difference is the new
  testid prop(s) and the rest is reformatting, it's a formatter artifact, not
  scope creep. Report this in the PR/Run Report rather than attempting a fix.
- If a reviewer wants this genuinely eliminated, the fix belongs upstream
  (get the file's on-`main` content reformatted to match the hook's own
  output in a separate, non-testid PR) — out of scope for a single-case
  testid commit.
