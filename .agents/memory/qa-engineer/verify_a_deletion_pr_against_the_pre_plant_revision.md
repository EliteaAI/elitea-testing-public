---
name: Verify a deletion PR against the pre-plant revision, not by reading the diff
description: For a "remove the thing X added" PR, diff the branch's file against X^ — identical output proves nothing rode along, which reading the diff cannot
type: feedback
aliases: [deletion pr review, revert review, pure deletion, ci repair review, blob hash inverse, planted probe removal]
tags: [area/review, type/technique]
created: 2026-09-07
updated: 2026-09-07
---

## The problem with reviewing a deletion by reading it

A two-line deletion is the easiest thing in the world to wave through, and waving
it through is exactly how an unrelated change rides along in the same commit. Reading
the rendered diff tells you what the diff *shows*; it does not tell you the result
equals the known-good prior state — a diff can delete the planted lines **and**
quietly alter a neighbouring assertion, and both hunks look reasonable in isolation.

## The check that actually settles it

When the PR claims "remove what commit `X` introduced", compare the *result* against
`X`'s parent directly:

```bash
git diff <X>^:<path> <branch>:<path> && echo ">>> IDENTICAL to pre-plant state"
```

Empty output is a proof, not an impression: the file is byte-identical to the state
before the thing was introduced, so nothing else changed in it — no weakened assert,
no touched decorator, no refactor.

**Corroborate with the blob hashes**, which are free and read straight off the two
commit patches. A true inverse shows the pair swapped:

- planting commit: `78adb6a67 -> ed5d3a2e6`
- repair commit:   `ed5d3a2e6 -> 78adb6a67`

Any other pair means the result is *not* the prior state, however plausible the diff read.

## Also worth running on a pure-deletion PR

`git diff <base>...<branch> -- <scope>/ | grep -E '^\+' | grep -v '^+++'` — "(no added
lines at all)" is the cleanest possible answer to *"is anything riding along?"*, and it
is stronger evidence than the two standing policy greps, which only ever inspect added
lines and are therefore trivially empty here. Say so in the verdict rather than
presenting an empty policy grep as if it did the work.

## Worked example — PR #2017 / #2016 (2026-09-07)

A planted `assert False` webhook probe (`30c2d1e08`) was deleted from
`test_ui_smoke.py`. The restored `test_page_loads` asserts only navigate + non-empty
title, which *looks* like someone gutted the test — the pre-plant diff is what proved
that this weak shape was its genuine prior state and not a weakening introduced under
cover of the repair.

Related: [[afs_claims_need_full_sweep_and_grep]] — same discipline: verify the claim mechanically, never from the narration.
