---
name: Run the matched pristine control before attributing a blast-radius red
description: A folder-wide run after a change will surface pre-existing reds; one control invocation on pristine base converts speculation into proof and prevents false bug filings
type: feedback
aliases: [blast radius, pristine control, did my diff break it, matched control, pre-existing red]
tags: [area/test-automation, type/triage-rule]
created: 2026-09-09
updated: 2026-09-09
---

## Rule

Before reasoning about whether your change caused a red in a blast-radius run,
**re-run the failing specs on pristine base with the diff absent.** Reasoning is only
trustworthy when the control agrees with it.

Worked case (#2079, 2026-09-09): `tests/ui/agent_hub/` = 7 red after a change whose
page-object diff was provably pure addition (`grep -c '^-[^-]'` -> 0). The control run
(6 specs, `automation/base`, ~2 min) reproduced 6 byte-identically:

- **5** were sanctioned-RED against already-open `#1215` (soft-asserted, expected — nothing to file)
- **1** was an untracked product `forwardRef` bug -> filed `#2102`
- the 7th was the identical drift on a sibling spec, already carded as `#2099`

Cost one invocation. Without it: either a false "my change broke 6 tests" rollback, or
5 duplicate bug filings against an issue that already exists.

## Two habits that make the control cheap

- **Classify before filing.** Map each failure to its cause first — `pytest.fail` bodies
  naming a `Known defect #N` are sanctioned-RED and owe nothing.
- **Dedup against open issues** before filing the residue (real-time list API, never
  `--search` — the index lags).

Related: [[hardcoded_count_drift_is_rarely_fixed_by_bumping_the_number]]
