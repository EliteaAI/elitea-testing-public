---
name: Repairing a neighbour spec leaves ITS AFS stale
description: A route/selector repair to an already-merged spec must amend that spec's own AFS in the same PR — reviewers only look at the dispatched cases' AFS files
type: feedback
aliases: [neighbour AFS drift, repaired spec AFS not amended, route repair AFS]
tags: [area/review, type/triangulation]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

A unit dispatched for cases A/B/C may legitimately repair a *fourth*, already-merged
spec on the way (here: #1794, the ELITEA-2272 Project Context spec still waited for
the retired `?view=create` URL). The repair changes that spec's **asserted
observable** — so the standing check "any selector/observable drift between AFS and
implementation must be reflected in an AFS docs commit in the same PR" applies to
the *neighbour's* AFS, which is not in the dispatch's AFS list and is therefore easy
for everyone (implementer, reviewer, lead) to skip.

## The check

After reading the diff, list every spec file it touches — not just the dispatched
cases' new ones — and grep each one's AFS for the strings the diff changed:

```bash
git diff <base>...HEAD --name-only -- automation/tests/ | sed 's#.*/##'
grep -n '<old value the diff removed>' test-specs/<feature>/*.md
```

A hit in an AFS that the diff did not touch is `CHANGES_REQUESTED`.

Related: [[afs_amendment_narrates_some_changes_leaves_others_unswept]]
