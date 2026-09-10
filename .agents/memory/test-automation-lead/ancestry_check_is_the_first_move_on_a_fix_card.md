---
name: The ancestry check is the FIRST move on a [FIX] card — before logs, before repro
description: One git command decides whether a CI red is real work or a promotion gap; running it first saved a whole session on #2173
type: feedback
aliases: [is-ancestor, promotion gap proof, fix card triage order, which artifact did CI run, 30-second proof]
tags: [area/triage, area/promotion, type/process]
created: 2026-09-10
updated: 2026-09-10
---

## The command, and why it goes first

```bash
git fetch origin
git merge-base --is-ancestor <repair-sha> <the-commit-CI-ran>   # from the card body's "Commit:" line
git merge-base --is-ancestor <repair-sha> origin/automation/base
git rev-list --count origin/main..origin/automation/base
```

`NO` + `YES` ⇒ **promotion gap, null code delta.** On #2173 (ELITEA-1866) this resolved the
entire card in under a minute: `556d39ed` / PR #2080 had repaired the exact failing assertion
**8 hours before** the CI run that filed the card.

I had been reaching for the job log first. The log is worth reading — but only to *confirm* the
signature matches the repair, which is a 2-line check once you already know the repair exists.
Reversing the order turns a 5-minute triage into a log-archaeology session.

## The tell inside the log, when you do read it

The failing assertion here was:

```
E   assert "{'total': 0, 'rows': []}" in '…{   "total": 0,   "rows": [] }'
```

**The value it wanted was right there.** A red where the expected data is visibly present in the
actual string is almost always a *serialization/format* drift already repaired somewhere — not a
product defect. Read both sides of an `assert x in y` before believing the summary.

## What the card body is worth

#2173's intake summary said *"the test assertion logic is comparing against the wrong element or
the UI is rendering the response in an unexpected format. Needs investigation."* Both halves wrong.
Same lesson as #2053/#2074/#2076: **the intake summary is a hypothesis, not evidence** — and it is
generated from the traceback by a model that has not seen `automation/base`.

## Don't stop at the gap — run the 3-question hazard check

See [[a_promotion_gap_fix_card_can_still_hide_real_work]]. On #2173 the answer was genuinely "no
hidden work" (2 of 3 negative), but establishing that is what separates a verified close from a
lazy one. Record the ruling on the *class* card (#1847 here), not on the case card.
