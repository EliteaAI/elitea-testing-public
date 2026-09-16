---
name: Promotion cherry-pick hidden sibling dependency
description: A clean auto-merge on a page object does not mean the picked method's class-field dependencies exist on main — grep every new symbol against main before running
type: feedback
---

**What happened (2026-09-16, card #2330, ELITEA-2022 promotion of `09219bb8f` onto `main`):**
`git cherry-pick -x` conflicted only on the import block, the AFS and `_surface.md`.
`automation/pages/pipelines_list_page.py` auto-merged cleanly, so it looked done — but the
picked commit's new `PipelinesListPage.wait_for_pipeline_absent()` reads
`self.empty_state_title`, a class field introduced by an UNPROMOTED sibling repair
(`6855dc3f4`, ELITEA-2024/#2118, PR #2148). Result on `main`:
`AttributeError: 'PipelinesListPage' object has no attribute 'empty_state_title'` in 12 s,
`reruns.json == {}`. Git cannot see a symbol dependency; a clean merge is not a green.

**Rule — before `cherry-pick --continue` on a promotion, for every method body the pick ADDS,
list the `self.<field>` / helper / constant names it references and check each on the TARGET:**
```bash
git diff --cached -- automation/ | grep -oE '^\+.*self\.[a-zA-Z_]+' | grep -oE 'self\.[a-zA-Z_]+' | sort -u
git log origin/main..origin/automation/base --oneline -S'<symbol>' -- <file>   # non-empty = unpromoted dep
```
A hit means the pick is not self-contained: report it to the lead with the owning commit —
either that commit joins the promotion or the lead decides. Never patch the field in by hand
(that is a silent partial promotion of another card).

**Resolution shapes that worked on the same pick:**
- Import-block conflict: resolve by USAGE in the resulting file, not by side. Both imports
  (`PlaywrightTimeoutError` — its only use was removed by the pick; `collect_console_errors` —
  only used in base's copy of another test) were unreferenced → dropped both, ruff clean.
- Case's own AFS: stage 3 (`git checkout --theirs`) was byte-identical to base and coherent;
  per-hunk "theirs" would have left half a code block because the analyst's earlier
  `docs(afs)` commit for the same card supplied the structure. Take the whole blob, declare it.
- Shared `_surface.md`: HEAD side empty → strip markers, keep the block; update the
  "Last updated" line to base's wording so the digest does not contradict its own top section.
- `.agents/memory/**` in a promotion pick: `UU` → `git checkout HEAD --`, `DU`/`A` →
  `git rm --cached` + `rm`. Never lands on `main`.
