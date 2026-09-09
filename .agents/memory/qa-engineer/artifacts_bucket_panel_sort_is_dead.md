---
name: Artifacts bucket panel's "most recent first" sort is dead code
description: sortBucketsByRecent reads created_at/updated_at; the API returns only creationDate, so the comparator is always NaN
type: project
aliases: [bucket order, sortBucketsByRecent, most recent first, 2126]
tags: [area/artifacts, type/product-defect]
created: 2026-09-09
updated: 2026-09-09
---

`SimpleBucketList.jsx` sorts through `sortBucketsByRecent` (`src/common/bucketSortingUtils.js`),
which reads `a.updated_at || a.created_at`. The list endpoint returns rows of
`{name, creationDate, size, retentionDays, isPinned}` — neither field exists, so both sides
are `NaN`, the comparator returns `NaN`, and per ECMA-262 that is treated as `+0`: the order
is left as received, i.e. **alphabetical**.

Verified live 2026-09-09: a freshly created `zzprobe…` bucket landed at DOM index 1203 of
1220; rendered order was byte-identical to the API order and fully sorted alphabetically.

`creationDate` is not a usable substitute as-is — its value tracks the listing time, not the
bucket's creation (a weeks-old bucket reported the current timestamp, and it changed between
two consecutive listings).

Filed as product bug #2126. Automation is unaffected (no virtualisation).
