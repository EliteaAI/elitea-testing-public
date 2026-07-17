---
name: A case with zero testid dependency simplifies the closure record — but still verify by grep
description: when a case's automation touches no first-party EliteaUI JSX (e.g. a third-party widget with no data-testid surface), the closure record's promotability row becomes N/A instead of the usual automation/testids-vs-main check — confirm this with a grep on the merged diff, don't just take the AFS's "permanent scope exception" claim at face value
type: feedback
---

## What happened (ELITEA-1799, issue #148, PR #608)

The Support Assistant widget is a third-party npm package
(`@eliteaai/elitea-assistant`) with no first-party EliteaUI JSX — the AFS
documented every handle as a "permanent scope exception," meaning
`add-data-testid` cannot remediate it (there's no first-party source file to
attach a testid to). This case's automation PR therefore touched zero
`data-testid` selectors of any kind — no new ones, no reused ones.

That made the closure record's usual "Testids" row (which normally lists
every testid the case's diff uses, checked against `main` vs
`automation/testids`) collapse to N/A — there's no `automation/testids` →
`main` promotion gap for this case at all, so it doesn't need a human
cherry-pick to become fully deployable-env-promotable.

## The lesson

Don't assume this from the AFS's own narrative alone. Verify it the same way
any other testid claim gets verified: `git diff <merge-base>..<merged-sha> --
<the case's touched files> | grep -c 'data-testid'` should be `0`. If it's
non-zero, the case DOES have a testid dependency and the normal
`automation/testids`-vs-`main` promotability check applies — don't let a
"third-party widget, no testid needed" narrative skip the verification step
just because it sounds plausible.
