---
name: AFS pass-criterion row names two side-channel checks, only one ships
description: The generic "no errors in any step" Coverage-Map row bundles 2+ mechanisms; verify EACH one has code, not just the row's disposition
type: feedback
aliases: [pass criterion row, no errors in any step, side channel coverage row, non-200 sweep]
tags: [area/review, type/triangulation-trap]
created: 2026-08-22
updated: 2026-08-22
---

## The trap

A TMS case's Pass/Fail block almost always ends with a generic criterion —
"All steps complete without errors" / "Any step produces an error → fail".
Analysts render it as ONE Axis-1 Coverage-Map row whose "Covered by" cell
lists **several** mechanisms at once, e.g.:

> `NON-200 SA CALLS == []` + console-error assertion (filtered per digest quirks 6/23)

and dispose it `covered`. The implementer then ships the mechanism that has an
obvious code shape (`assert console_errors == []`) and silently drops the one
that needs its own collector (a blanket non-200 sweep over the feature's HTTP
calls). Nothing else in the diff names the dropped check, so it leaves no
trace: the row still reads `covered`, the test is green, and the AFS-vs-diff
scan passes because *a* matching assertion exists.

Seen on ELITEA-2423 (support-assistant history after refresh, 2026-08-22): the
row promised a blanket `NON-200 support_assistant calls == []` alongside the
console-error assertion; only the console assertion shipped, while the AFS was
amended in the same PR for five *other* implementation-time corrections.

## The check

Split every Coverage-Map cell on `+` / `and` / `,` and grep the diff for
**each** conjunct separately. A row is only satisfied when every mechanism it
names has code. The "Asserted where" column is the tell: when it points at a
block that does not exist in the spec (`side-channel block`, `setup`,
`teardown`) rather than a real `allure.step`, at least one conjunct is missing.

Resolution is two-way (reviewer contract § Triangulate): implement the missing
check when it genuinely strengthens the case's own criterion (usually the right
call — these sweeps are ~6 lines on an existing `page.on("response")` handler),
or amend the AFS row to the narrower disposition. Never leave the row claiming
more than the code does.

Related: [[afs_axis2_claim_needs_grep_not_just_row_presence]] ·
[[afs_coverage_map_narrow_fix_leaves_sibling_rows_stale]] ·
[[afs_amendment_narrates_some_changes_leaves_others_unswept]]
