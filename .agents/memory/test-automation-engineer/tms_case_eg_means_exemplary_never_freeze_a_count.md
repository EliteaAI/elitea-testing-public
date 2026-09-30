---
name: An "e.g." in a TMS case is exemplary — never freeze a count off it
description: Case text listing items with "e.g." licenses asserting those items literally, never an exact count of the set they came from.
type: feedback
aliases: [e.g. in case text, exemplary vs enumeration, exact count assertion, to_have_count from case text, frozen CMS count]
tags: [area/assertions, type/case-reading]
created: 2026-09-30
updated: 2026-09-30
---

## The rule

When a TMS step names items with **"e.g."**, it is giving a worked example of a
category, not enumerating the set. That licenses asserting those named items
**literally**; it never licenses `to_have_count(len(named_items))` on the set
they were drawn from. An exact count derived from an "e.g." list is an invariant
the *spec* invented, and it is attributed to the case in review — which is how it
survives.

## The test to apply

Ask what the exact count uniquely catches that the literal named-item
assertions do not:

- item **REMOVED** → already caught, the named-item assertion fails.
- named item **DUPLICATED** → already caught, Playwright strict mode fails on a
  multi-match locator.
- item **ADDED** → the only unique catch. On a backend/CMS-served list that is a
  *content change, not a defect* — i.e. pure rot risk.

If "added" is the only unique catch and the producer is CMS/config data, drop the
count and keep the literal assertions. Coverage is unchanged; the rot vector is
gone. Say so in the docstring — an undeclared relaxation is indistinguishable
from a weakened assertion.

## Consistency smell that reveals it

If the same spec already *refuses* to freeze sibling data because it is
CMS-served, and freezes one subset's count anyway, the freeze is almost
certainly unexamined — especially when both arrive in the **same** backend
response.

## Worked case

ELITEA-2219, step 7: *"Verify all the cards (e.g.INTERACTIVE TOURS) are visible
with their links: (e.g. \"Sidebar Interactive Tour\" and \"Chat Interactive
Tour\")"*. Both `e.g.`s are exemplary. The spec froze that card at
`to_have_count(2)` while deliberately not freezing the other 19 links from the
same `useGetResourcesConfigQuery` response. Relaxed on the lead's fix round;
both named links stayed literal.

Related: [[afs_is_a_work_order_not_gospel]]
