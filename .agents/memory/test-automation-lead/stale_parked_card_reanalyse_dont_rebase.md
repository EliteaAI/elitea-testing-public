---
name: A parked card resumed weeks later gets re-analysed, not rebased
description: When a human un-parks an old card, re-run the case fresh — a branch far behind base is a rewrite, and its findings are unverified claims
type: feedback
aliases: [stale branch, resume blocked card, rebase old PR, parked card, un-park, proceed instruction]
tags: [area/orchestration, type/decision]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

A card parked `Blocked` and dragged back to `Approved` weeks later is a **fresh delivery**, not a
continuation. Before touching the old branch, measure it:

```bash
git rev-list --left-right --count origin/<base>...origin/<old-branch>
```

Two independent reasons to re-run rather than rebase, and either alone is decisive:

1. **Code drift.** Hundreds of commits behind means the shared substrate (page objects, fixtures,
   conftest) has moved under the branch. Rebasing is a rewrite with none of a rewrite's review.
   *Worked case: ELITEA-2094 / #297 was 813 commits behind — the `chat-remaining` campaign had since
   landed nearly every page-object method the old branch hand-rolled.*
2. **Evidence decay.** Every defect the old attempt filed, every environment fact it recorded, and
   its whole disposition are **claims as of that date**. The product may have been fixed; the fact
   may never have been true. Re-verify each blocker live before reasoning from it.

## The intake-note channel

Hand the history to the analyst *as context in the case snapshot*, explicitly labelled **reference
input, not conclusions** — prior AFS path (`git show <branch>:<path>`), open defect table with
states, verbatim park reasoning, the open question the analysis must answer. Then let the analyst
reach its own verdict. This works: on #297 the analyst both used the note and **retired a stale fact
it carried** (the July claim that project 399 "has zero pipelines and MCPs" — false; the fixtures
provision into 399 fine).

**Do not carry a prior environment fact forward unverified.** Restating one in an intake note gives
it authority it has not earned. Mark each as *re-verify, don't assume* — or leave it out.

## Do not prescribe technique in that note

State the observable and the constraint; let the analyst determine fidelity. A lead's dispatch is the
strongest signal in the pipeline, and a technique suggested there is judged by nobody
(`.agents/role-overrides.md` § Orchestrator slot).

Related: [[blocked_case_afs_still_lands]]
