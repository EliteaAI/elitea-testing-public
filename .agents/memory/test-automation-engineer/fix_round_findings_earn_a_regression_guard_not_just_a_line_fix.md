---
name: Fix-round findings earn a regression guard, not just a line-fix
description: 3rd occurrence this batch (ELITEA-2607/2609/2610) — pair the one-line fix with a static/functional unit test that reproduces the exact defect shape
type: feedback
---

Three separate fix-round dispatches in `skills-remaining-w4` hit the SAME
review pattern: a static/mechanical defect (a stale `@allure.issue` filename
twice — ELITEA-2607, ELITEA-2609 — and a truncate-after-concat name-uniqueness
bug — ELITEA-2610). In each case the fix itself was a one-line correction, but
the higher-value move was pairing it with a small `automation/tests/unit/`
test that:

1. Imports/parses the *actual* fixed artifact (the live spec module, or its
   source via `ast`) rather than re-describing the fix in prose.
2. Reproduces the ORIGINAL buggy shape inline and asserts the fix differs
   from it — proving the guard would have caught the defect, not just that
   it currently passes.
3. Runs in seconds, no browser — cheap enough to run on every future PR.

Precedent files: `test_skill_agent_interaction_allure_issue_links.py`
(ast-parses `@allure.issue` URLs, checks against the sibling TMS repo on
disk), `test_skill_version_selection_behavior_name_uniqueness.py` (imports
the spec module, checks names against a reconstructed buggy shape).

**When a reviewer flags a mechanical/structural finding (naming, a link
target, a length cap, a copy-paste artifact) rather than a live-product
behavior gap: default to writing the guard test alongside the fix, in
`tests/unit/`, not just the fix.** It costs one extra file and pays for
itself the next time the same shape recurs anywhere else in the suite.

## The boundary (learned the hard way — ELITEA-1968 PR #1670 round 2)

**The guard must parse an EXECUTABLE artifact.** Every precedent above does:
the spec module's own source (via `ast`), its `@allure.issue` URLs, the
imported module's test names. That is not incidental — it is the line.

A guard that asserts the **prose of a markdown document** (an AFS, a surface
digest, a README) is **doc-lint, not coverage**, and is `CHANGES_REQUESTED`:

- it reds the pytest suite for a documentation edit — reword, rename or move
  the doc and the run goes red with no product cause. The merge gate cannot
  classify that red: it is not sanctioned-RED (no open defect), so it blocks;
- two-sided guards make it worse — the inverse branch starts *demanding* the
  prose it previously forbade;
- it appears in no AFS Coverage Map, so it ships as an undeclared artifact.

So: a reviewer finding of the form **"the AFS/docstring over-claims"** is closed
by **editing the document**. Nothing else is owed — do not reach for this entry.
Reach for it when the defect lives in code the guard can import or `ast`-parse.
Real doc-lint, if wanted, is a canon `question` card + a lint step outside the
product test suite.

Related: [[declaring_an_afs_addition_dropped_does_not_rescind_earlier_rows]]
