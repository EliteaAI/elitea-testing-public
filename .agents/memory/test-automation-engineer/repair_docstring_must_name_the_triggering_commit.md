---
name: A repair docstring must name the product commit that broke the test, not just the mechanism
description: Explaining the mechanism without dating it reads as "this test was never sound"
type: feedback
---

When repairing a merged test that went red (`adjust-automated-test`), the fix
docstring naturally explains **the mechanism** — what the product does now and
why the old reach no longer works. That is necessary and not sufficient.

Without the **trigger** — the product commit, its ticket, its date, and what
the behaviour was *before* it — the docstring reads as though the spec was
always racy and merely got lucky for weeks. That quietly indicts the original
author, the reviewer, and the merge gate, and it invites a future reader to
distrust the whole spec rather than the one changed dependency.

The shape that works (ELITEA-1955 / #1890):

> Guards a first-open-only load race **introduced by a product change**, not by
> a flaw in the spec: `EliteaAI/EliteaUI@94a61b81` (EL-6351, 2026-08-26), which
> landed one day before this spec first went red in CI. Before it,
> `useLibraryToolkits` gated its query on `skip: !projectId` alone, so the
> request fired on **mount** … the spec was sound when written and passed its
> merge gate honestly.

Two operational notes:

- **Verify the sha yourself before writing it.** `git -C ../EliteaUI log -1 <sha>`
  for the date and body, plus `git log -1 -S"<the new symbol>" origin/main -- <file>`
  to prove *that* commit introduced the mechanism (not merely touched the file),
  and `git merge-base --is-ancestor <sha> origin/main` to prove it shipped.
  Reading the pre-change file (`git show <sha>^:<file>`) is what turns "the query
  used to fire on mount" from a plausible story into a checked fact.
- **The AFS carrying the attribution is not enough.** Someone debugging this
  test six months from now opens the test file, not `test-specs/`. Attribution
  belongs in both.

(Correction received from the lead, 2026-08-28, on an otherwise-approved fix.)
