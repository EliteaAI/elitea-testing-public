---
name: A covering-spec repair inside an extend-existing unit leaves the COVERED case's AFS and docstrings stale
description: extend-existing units that repair the covering spec must sweep that spec's own docstrings + its case's AFS, not just the constant they changed
type: feedback
aliases: [extend-existing repair drift, covering spec docstring stale, KPI card count 10 vs 16, AFS not amended]
tags: [area/test-automation, type/triangulation-trap]
created: 2026-08-28
updated: 2026-08-28
---

## The pattern

An `extend-existing` unit legitimately repairs the covering spec first (the product moved, the
merged spec was already red). The repair updates the **assertion constant** — and stops there.
What stays behind, all now stating a falsehood:

1. the covering spec's **module docstring** ("live view has 10 cards" while the constant lists 16),
2. an unrelated **test docstring** in the same file repeating the old number,
3. the **covered case's own AFS** (`l2_..._<COVERED-ID>.md`) — Coverage Map row, Expected Results,
   Known Defects — none of which is in the extending unit's diff.

Seen 2026-08-28 on ELITEA-2329 extending ELITEA-2313 (`test_analytics_user_detail_view.py`): the
16-card repair was correct and source-verified, but the file's own narrative and ELITEA-2313's AFS
still said 10.

## The check, as a reviewer

When a diff repairs an assertion in a spec whose case is NOT in the unit under review:

```bash
grep -n "<old value>\|<old count>" <the repaired spec>            # docstrings in the same file
grep -rn "<old value>" test-specs/<feature>/*_<COVERED-ID>.md      # the covered case's AFS
```

Both must come back empty, or the PR owes a `docs(afs):` amendment in the same PR (reviewer
contract: "any selector / observable drift between AFS and implementation must be reflected in an
AFS docs commit in the same PR"). A declared repair in the *extending* case's AFS does not
discharge this — it documents the change where the person reading the *repaired* case will never
look.

Related: [[afs_coverage_map_drifts_after_a_fix_round]] · [[afs_drift_check_the_whole_document_not_just_the_last_fixed_section]]
