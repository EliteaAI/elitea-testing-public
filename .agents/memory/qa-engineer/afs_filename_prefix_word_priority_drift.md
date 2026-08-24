---
name: AFS filename prefix must be numeric (l1_/l2_/l3_), and renaming one strands the spec's docstring pointer
description: Recurring drift — AFS files land as lhigh_/lmedium_ instead of the repo's numeric l1_/l2_/l3_ convention; the rename fix then breaks the "AFS:" pointer in the shipped spec's module docstring, which lives under automation/ and is often outside an AFS-only dispatch's boundary.
type: feedback
aliases: [afs filename prefix, lhigh, lmedium, l1_ l2_ l3_, afs rename, afs docstring pointer]
tags: [area/afs, type/convention]
created: 2026-08-24
updated: 2026-08-24
---

## The convention, measured

`test-specs/` filename prefixes are **numeric**, mapped from the TMS case's
`priority:` field:

| TMS `priority:` | prefix | pytest marker |
|---|---|---|
| high | `l1_` | `p1` |
| medium | `l2_` | `p2` |
| low | `l3_` | `p3` |

Counted 2026-08-24 across `test-specs/`: **217 × `l2_`, 168 × `l3_`, 39 × `l1_`**
against **3 × `lmedium_`, 2 × `lhigh_`**. The word form is drift, not a variant.

## It recurs, and it recurs in two layers

The ELITEA-2231 closure record (issue #1397) already records this being fixed
once (`l3_` → `l2_`). The onboarding-w2 batch then shipped four more word-form
files (2235, 2236 as `lhigh_`; 2232, 2241 as `lmedium_`). Note the second layer:
the prefix can be wrong *while the file's own `**Priority:**` line and the
shipped `pytest.mark.p*` are both correct* — that was the case for all four
here. So the prefix is a **third** thing to check, independent of the
AFS-Priority-vs-pytest-marker check in
[[priority_marker_drift_afs_vs_pytest_mark]].

## The trap when you FIX it: the rename strands a pointer

Every shipped spec's module docstring carries an `AFS:` line naming the AFS by
full path:

```python
"""UI test — ...
TMS: ELITEA-2236
AFS: test-specs/onboarding/l1_onboarding_tips_fullscreen_expand_collapse_ELITEA-2236.md
```

`git mv` on the AFS silently invalidates that pointer, and the spec lives under
`automation/` — which an AFS-hygiene dispatch is typically forbidden to touch.
So the rename and its own follow-up land in **different** boundaries.

**Always run the sweep after any AFS rename** and report what you cannot fix:

```bash
grep -rn "<old-filename-stem>" . --exclude-dir=.git
```

Check three places: the shipped spec's docstring (`automation/tests/**`), the
surface digest (`test-specs/<feature>/_surface.md` § Related AFS), and sibling
AFS cross-references. `.agents/automation/**` hits are noise — that path is
gitignored run-receipt scratch, not a repo reference, and rewriting a receipt
falsifies an archive.

Related: [[priority_marker_drift_afs_vs_pytest_mark]]
