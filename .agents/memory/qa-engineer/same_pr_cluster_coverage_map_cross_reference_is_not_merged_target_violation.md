---
name: Same-PR cluster Coverage Map cross-reference is not a merged-target violation
description: A Coverage-Map row saying "already-covered by sibling case X" is fine when X ships in the SAME PR/unit (shared fate) — the merged-target rule targets cross-UNIT dependencies, not intra-cluster ones.
type: feedback
---

Reviewed PR #1543 (ELITEA-2142/2143/2145, drag-and-drop conversation<->folder,
3 TMS cases as 3 separate AFS/test methods in ONE PR because they were
cluster-analysed together). ELITEA-2142's AFS Coverage Map row 3 disposes
"Target folder becomes visually highlighted" as `already-covered *(by
ELITEA-2143, once merged)*`.

At first glance this looks like the role-overrides.md "Covered-by rows... a
row pointing at... a same-batch AFS (merged-target rule violation), is
CHANGES_REQUESTED" trap. It is NOT a violation here: ELITEA-2143's own test
is in the identical PR/commit/branch as ELITEA-2142's — they merge to
`automation/base` atomically, in the same event. The merged-target rule
protects against a case being marked safe based on a DIFFERENT unit that
might never land or might land with different scope (different PR, different
fate). A same-PR cluster cross-reference carries no such risk.

Distinguish by asking: "if this PR's merge fails/is dropped, does the
covering row's claim still hold?" — same-PR sibling: irrelevant, both die or
both live together. Different-PR/different-batch sibling: real risk, flag it.

Still verify the covering assertion actually exists at the claimed step (the
standing "verify against assertions, not existence" check) — that part of
the check is unaffected; only the "different unit" trap doesn't apply here.
