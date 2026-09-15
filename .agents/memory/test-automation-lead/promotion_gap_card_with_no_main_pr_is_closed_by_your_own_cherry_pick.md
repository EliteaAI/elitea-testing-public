---
name: A promotion-gap [FIX] card with NO existing PR to main is closed by cherry-picking the base repair yourself — merge-tree first, stash your memory files, no dispatch when clean
description: Third use of the da663ef template path (#2290, ELITEA-1902): the lead cuts AI_AQA/fix-… from origin/main, cherry-picks -x the base squash, gates 3× on DEV, squash-merges, back-merges — ~20 min, zero dispatches when the pick is conflict-free
type: feedback
aliases: [cherry-pick repair to main, no PR to main yet, AI_AQA branch from main, merge-tree cherry-pick dry run, stash memory before checkout, promotion path conflict-free]
tags: [area/promotion, area/merge-gate, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---
## The shape (#2290, ELITEA-1902 — 5th card for one signature)
#2286 had a PR to `main` already; #2287 conflicted on `client.py`. #2290 is the plain case: repair on base
(`803ae269a`), nothing on `main`, and the pick is clean. Whole card = ~20 min, no subagent:

```
git merge-tree --write-tree --merge-base=<sha>~1 origin/main <sha>   # rc 0 ⇒ the pick will be clean
git stash push -u -- .agents/memory/test-automation-lead              # tracked memory files differ main↔base and BLOCK checkout
git checkout -b AI_AQA/fix-<case> origin/main && git cherry-pick -x <sha>
git commit --amend  # subject → "AI_AQA: <original>", add "Refs #card #siblings", keep the (cherry picked from …) trailer
git diff origin/automation/base -- <spec> <AFS>                       # must be EMPTY
git diff origin/automation/base -- <shared file> | grep '^+' | grep -v '^+++'   # lines MAIN has that base lacks — read them; they are other unpromoted base repairs, not yours
push → PR to main (`Refs`, never `Fixes`) → gate the checked-out candidate 3× via -p devenv → gh pr merge --squash --subject "AI_AQA: …"
git checkout automation/base && git merge origin/main && push       # then: git rev-list --left-right --count origin/main...origin/automation/base → 0 N
git stash pop
```

## Why no dispatch
A cherry-pick of an already-reviewed, already-gated commit is merge mechanics (the lead owns the merge gate), not
code authoring — the no-edit guardrail bites only when the pick CONFLICTS (then a fix-only implementer resolves it,
per [[promotion_gap_cherry_pick_to_main_conflicts_on_grown_shared_files]]). Run `merge-tree` first so you know
which case you are in before touching the tree.

## Two details that cost a turn each
- **Your own memory files block the checkout.** `.agents/memory/<role>/` is tracked and differs between `main`
  and `automation/base`; an uncommitted edit there makes `git checkout -b … origin/main` refuse. Stash that path
  (`-u` for new notes) and pop after returning to base.
- **`git diff origin/automation/base -- <shared page object>` is NOT expected to be empty** — base has grown the
  file with other cases' methods. The check that matters is the `+` lines (what main has that base lacks): read
  them and confirm they are pre-existing main code, not something your pick added.

## Disposition wording
No `duplicate` label — the card delivered the promotion. Say explicitly in the closure record that the next nightly
runs the repaired spec, so a further ELITEA-<id> filing is a NEW signature. `automation_pr` in the TMS stays the
`automation/base` PR (per `.agents/test-automation.yaml`); the `main` PR goes in the closure record only.

Related: [[intake_template_now_says_lead_merges_test_only_repairs_to_main]] ·
[[promotion_gap_cherry_pick_to_main_conflicts_on_grown_shared_files]] · [[the_devenv_plugin_is_the_factory_safe_dev_gate]]
