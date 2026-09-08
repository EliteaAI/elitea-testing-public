---
name: A mass testid loss in the sync guard can be a deliberate dead-code deletion
description: Before restoring anything, find where the lost testids LIVED — a whole-tree deletion upstream is row 2, not row 1
type: feedback
aliases: [testid-loss guard, comm -23, _legacy deletion, 131 testids, sync guard fired]
tags: [area/sync, type/triage]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

`sync-base-branches`' testid-loss guard fires and the instinct (and the skill's
first table row) is **restore**. On 2026-09-09 it reported **131 lost** (1177 -> 1077)
on EliteaUI — and restoring even one would have been wrong.

## What it actually was

Every one of the 131 lived under `src/[fsd]/widgets/evaluation/ui/_legacy/`, which
`origin/main`'s commit `18b76777` ("Remove legacy evaluation code") deleted on purpose —
41 files, with a written reachability analysis: `EvaluationTab` was exported from a
barrel but *rendered by nothing*, so the whole tree was unreachable. Our testids were
sitting on dead code that never rendered.

That is triage table **row 2** (deliberate removal: do NOT restore), not row 1
(merge dropped ours: restore).

## The discriminator — one command, run it first

Locate the pre-merge home of the lost testids before deciding anything:

```bash
while read t; do git grep -l -F "\"$t\"" ORIG_HEAD -- src/; done < /tmp/lost.txt \
  | sed 's/^ORIG_HEAD://' | sort | uniq -c | sort -rn
```

- Clustered in one tree that `origin/main` no longer has ⇒ deliberate deletion.
- Scattered across files that still exist on main ⇒ the merge dropped ours ⇒ restore.

Then confirm the count of lost testids living OUTSIDE the deleted tree is **0**, and
check the blast radius in the test repo (`grep -rnF -f /tmp/lost.txt automation/ test-specs/`).
Here: 0 outside, 0 referenced ⇒ safe to push.

## Two guards on the reasoning

- **A 0-reference result needs a positive control.** `grep -F -f` with 131 patterns
  returning 0 looks identical to a broken invocation. Re-run with known-referenced
  testids appended; if the hit count is unchanged, the zero is real.
- The skill permits the push on exactly this condition — *"once comm is empty **or every
  difference is a confirmed deliberate removal**"*. Confirm every one, then say so.

Related: [[main_and_automation_base_have_diverged_badly]]
