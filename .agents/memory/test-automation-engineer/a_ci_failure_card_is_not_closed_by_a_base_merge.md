---
name: A CI-failure card is not closed by an automation/base merge
description: The GHA smoke/regression workflows run against main, so repairing a spec on automation/base leaves the failing CI card red until a human promotes
type: feedback
aliases: [ci failure card, main vs base ci, smoke red on main, promotion gap, intentional failure probe]
tags: [area/ci, type/trap]
created: 2026-09-07
updated: 2026-09-07
---

## The trap

An intake-generated `[Fix] CI Failure …` card names a workflow run (e.g. "UI Tests DEV
Stable **[main]** [smoke] #102"). The obvious loop is: fix the spec, PR into
`automation/base`, merge, close the card. **That loop never turns the card green.**

`.github/workflows/test-ui-*.yml` run against **deployed envs from `main`**
(`.agents/testing.md` § CI integration). `automation/base` has no CI at all. So the
repair lands on a branch the failing workflow does not read.

## What to do instead

1. Read the workflow ref in the card title / run URL **before** planning the fix —
   `[main]` in the title is the tell.
2. Repair on `automation/base` as normal (that is still the right base — never PR `main`).
3. **Say explicitly in the PR body and the card comment that the merge does not close
   the CI failure**, and name the human-owned `automation/base` -> `main` promotion as
   the unblock. Same shape as the testid promotability row in a closure record.
4. Verify the claim rather than assuming — the one-liner is cheap:
   `git grep -n "<symptom>" origin/main -- <path>`

## Worked example — #2016 / PR #2017 (2026-09-07)

`test_ui_smoke.py::test_page_loads` carried a hard-coded
`assert False, "INTENTIONAL FAILURE: Testing webhook pipeline integration"`, planted as
a webhook probe in EliteaAI/elitea-testing-public@30c2d1e08 and present **identically on
`origin/main` and `origin/automation/base`**. Deleting it went green locally in 21.76s,
but `git grep` confirmed `main` still carried both lines at merge time — so #2016 stays
open pending the human promotion, and saying so was part of the deliverable.

Note the failure class: a planted probe is neither a flake nor a product defect. It is
deterministic and deliberate, so the § Merge gate sanctioned-RED reasoning does not apply
— there is no defect to link. Delete it; do not soften it.

Related: [[testid_provenance_composed_handles_need_caller_side_diff]] — the same "verify against origin/* with a fresh fetch, never assume" discipline, applied to testid provenance.
