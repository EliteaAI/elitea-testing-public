---
name: Verify PR merged before trusting any workflow-reported unit outcome
description: gh pr view <number> on every unit's declared PR, before accepting the workflow's outcome label — whether it says automated, blocked, or anything else — is cheap and catches both false-positives and false-negatives
type: feedback
---

## The pattern, generalized

Two separate incidents in the `pipelines-remaining` campaign (2026-08-09) showed the same root
cause from opposite directions:

1. **wave-03**: the workflow's own report labeled `ELITEA-2027` `blocked` ("subagent completed
   without calling StructuredOutput") — a false NEGATIVE. Ground truth (`gh pr view 1344` → MERGED,
   plus the test genuinely present and green) proved it had actually succeeded.
2. **wave-01/02 (recurring)**: the workflow's report labeled units `merged-ungated` when the gate
   simply hadn't finished — technically accurate labeling, but easy to under-trust into treating as
   a failure if you don't separately confirm the merge itself is real via git/gh.

Both directions point to the same fix: **the workflow's own narrated outcome for a unit is not
sufficient evidence, full stop — in either direction.** Before accepting ANY unit outcome
(`automated`, `blocked`, `merged-ungated`, `already-covered`), check the two cheap, independent
facts that can't lie:

```bash
gh pr view <declared-pr-number> --repo <repo> --json state,mergedAt   # is it ACTUALLY merged?
git log --oneline <trunk> | grep <case-id>                            # is the merge commit really there?
```

## Why this is cheap enough to always do

One `gh pr view` call per unit, batched into a single loop over all of a wave's declared PR
numbers, costs seconds. Compare that to the cost of NOT doing it: wave-03's false-blocked label
would have caused ELITEA-2027 to be silently dropped from the TMS back-write and re-queued for a
future wave — duplicate work, or worse, a permanently-lost case if nobody re-checked. Running this
check on every wave (not just when something looks suspicious) is what caught it — it wasn't
flagged by anything else in the pipeline.

## Rule

Before writing ANY wave-closing artifact (TMS back-write, closure comment, campaign-card update),
loop `gh pr view` over every unit's declared PR number in that wave's report and confirm
`state: MERGED`. Cross-reference against `git log <trunk>` for the actual merge commit. Treat a
mismatch between the report's claimed outcome and this ground truth as a report bug to fix by hand
(see `report_case_outcome_can_falsely_say_blocked_for_an_already_merged_case.md` for the specific
correction mechanics), not as something to re-run or ask about.
