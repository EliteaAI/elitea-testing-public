---
name: State-attribute handles (data-severity, data-expanded) are FALSE NEGATIVES in the two-stage provenance grep
description: The closure-record stage-2 filter needs data-testid|testid[:=] on the SAME LINE, so a sibling state attribute on its own JSX line reports "not on main" even when it is — confirm those by reading the file, never by grep
type: feedback
aliases: [data-severity provenance, state attribute grep false negative, two-stage grep false negative, data-expanded provenance]
tags: [area/testids, type/provenance]
created: 2026-08-28
updated: 2026-08-28
---

## The trap (ELITEA-2348/2349, PR #1911, fix round 3, 2026-08-28)

`.agents/testing.md` § Locator policy requires state to be asserted as a
`data-*` attribute filter on a stable testid — e.g.
`[data-testid="toast-alert"][data-severity="error"]`. So a provenance row
legitimately has to cover the **state attribute**, not just the testid.

But the canonical two-stage grep from `.agents/workflow.md` § Closure record is:

```bash
git grep -- "$t" origin/main -- src/ | grep -qiE '(data-testid|testid[[:space:]]*[:=])'
```

Stage 2 requires a testid token **on the same line as the hit**. In JSX the state
attribute sits on its own line, one below the testid:

```jsx
<Alert
  data-testid="toast-alert"        // line 60 — passes stage 2
  data-severity={severity}         // line 61 — stage-1 hit, stage-2 DROPPED
```

So probing `data-severity` returns `main:no  testids:no` — which reads as
"needs-adding" and is equally consistent with "the filter can't see it". Truth:
`Toast.jsx` is **byte-identical on both refs** and `data-severity` has been on
`main` at `:61` all along.

## The check that works

Never probe a state attribute through the stage-2 filter. Diff or read the file:

```bash
git diff --stat origin/main origin/automation/testids -- src/components/Toast.jsx  # empty ⇒ identical
git show origin/main:src/components/Toast.jsx | grep -nE 'toast-alert|data-severity'
```

Same class as the composed-testid trap ([[composed_testid_provenance_grep_the_composing_source]]):
a 0-hit result from a grep that **structurally cannot** see the thing is not evidence
of absence. Distinguish "grep says no" from "grep cannot answer" before writing a row.

## Why it matters in this direction specifically

The composed/state false negative pushes a row toward `needs-adding` — i.e. it
manufactures phantom testid work and understates promotability. The opposite error
(a false `on-main ✓`) overstates it. Both corrupt the closure record's promotability
table; this one is the less obvious of the two because it errs "cautiously" and so
nobody re-checks it.

Related: [[testid_provenance_composed_handles_need_caller_side_diff]] ·
[[afs_on_main_provenance_claim_needs_two_ref_grep]]
