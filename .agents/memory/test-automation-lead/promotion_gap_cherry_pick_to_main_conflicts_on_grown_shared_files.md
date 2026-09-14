---
name: Cherry-picking one base repair onto main conflicts wherever base has GROWN the same shared file — and the conflict hunk can smuggle a neighbour
description: A [FIX] promotion by cherry-pick is not "apply one commit"; on files like automation/api/client.py that base has extended, both the cherry-pick and the back-merge conflict, and the hunk carries unrelated base code that must be dropped — diff the repair commit itself to know what belongs
type: feedback
aliases: [cherry-pick conflict client.py, promote repair to main conflict, list_credential_types smuggled, back-merge conflict main to base, AI_AQA fix branch conflict, template promotion mechanics]
tags: [area/promotion, area/merge-gate, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## What happened (#2287, ELITEA-1901, 14th [FIX] filing)

Second use of the `da663ef` intake-template path (after #2286): promote a single reviewed, 3×-gated
`automation/base` repair (`76cc6fa1f` / PR #2125) to `main` by cherry-pick on an `AI_AQA/fix-…`
branch, gate on DEV, squash-merge, merge `main` back down.

Unlike #2286 (whose PR to `main` already existed and was merge-tree clean), this one **conflicted
twice on the same file**, `automation/api/client.py`:

1. **Cherry-pick onto `main`**: the repair added ONE method (`list_models`) next to a method that
   exists only on base (`list_credential_types`, ELITEA-1966). Because main lacks that neighbour,
   git could not place the hunk and offered `HEAD = empty` vs `theirs = BOTH methods`. Taking
   "theirs" would have shipped ELITEA-1966's method to `main` under an ELITEA-1901 title.
   **The proof of what belongs is the repair commit itself:**
   `git show <sha> -- <file> | grep -E '^\+\s+def '` → only `list_models`.
2. **Back-merge `main → automation/base`**: the squash's `list_models` now sits where base has
   `list_credential_types`, so the add/add conflicts again. Resolution is base's copy verbatim,
   proven mechanically: `git diff origin/automation/base origin/main -- <file> | grep '^+' | grep -v '^+++' | wc -l` → **0** (main ⊂ base).

Both resolutions went through a fix-only `test-automation-engineer` dispatch (the no-edit
guardrail covers `automation/api/` too). ~2 min and ~150k tokens each — cheaper than the 6 prior
guardrail violations cost in rework.

## Why base's shared files will keep doing this

`client.py` on base carries **8 methods** main lacks (guardrails, folders, credential types,
bucket pin …). Every per-spec cherry-pick that touches a shared framework file lands next to
some of them. Expect this on `client.py`, `base_page.py`, `conftest.py`, `data_fixtures.py` —
anything append-at-the-end that many cases have grown. Spec/AFS files rarely conflict (one case
owns them).

## Procedure that worked

```
git checkout -b AI_AQA/fix-<case> origin/main
git cherry-pick -x <repair-sha>            # conflict → dispatch: keep ONLY the repair's own hunks
# amend subject to "AI_AQA: <original subject>"; body + (cherry picked from …) trailer stay
# verify: git diff origin/automation/base -- <spec> <AFS>  → EMPTY
#         git diff origin/automation/base -- <shared file> | grep '^+.*def '  → EMPTY
push → PR to main with `Refs #…` (never `Fixes`) → 3× DEV gate via -p devenv → gh pr merge --squash
git checkout automation/base && git merge origin/main   # conflict → dispatch: base's copy verbatim
git rev-list --left-right --count origin/main...HEAD    # must read 0 <N>
```

Also: `git commit --no-edit` on a merge commits the **whole index** — git auto-merges and stages
memory logs, and they ride into the merge commit unless named. Tell the subagent what is staged.

Related: [[intake_template_now_says_lead_merges_test_only_repairs_to_main]] ·
[[no_edit_guardrail_repo_agnostic]] · [[dev_gate_discipline_for_fix_cards]] ·
[[the_devenv_plugin_is_the_factory_safe_dev_gate]]
