---
name: An AFS value rename needs a grep of the whole AFS for the OLD literal
description: Renaming a test-data value in AFS § Test Data leaves the same literal stale in § Test Steps — grep the file, don't edit the section you were looking at
type: feedback
aliases: [afs doc-sync stale literal, test data rename afs, sibling section stale]
tags: [area/afs, type/doc-sync]
created: 2026-08-22
updated: 2026-08-22
---

## What happened

ELITEA-1970: the generated Display Name was shortened from
`autotest_cred_testconn_${ts}` (33 chars) to `autotest_cred_conn_${ts}` after
the field's real `maxLength = 32` silently truncated it and cost a run. The
AFS § Test Data row was updated; **§ Test Steps step 1 kept the old literal**.
The AFS then contradicted itself AND its stale half was the exact value the
product truncates — a reader following the steps would re-create the failure.
Caught at review, cost a fix round.

## The rule

When a value changes anywhere in an AFS, `grep` the whole file for the OLD
literal before committing the amendment. Editing "the section I was looking
at" is how sibling sections go stale — the same class as
[[afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row]].

Applies equally to the Phase-6 doc-sync pass: it is a **file-wide** sweep for
every value the implementation changed, not a spot-check of the row that
motivated the change.

Related: [[afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row]] · [[afs_is_a_work_order_not_gospel]]
