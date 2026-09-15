---
name: A cherry-pick to main must check every symbol the spec calls, not just whether the pick applies cleanly
description: A conflict-free pick can still ship a spec that imports a base-only method — grep each call against origin/main first; a missing one is a verbatim port, dispatched
type: feedback
aliases: [cherry-pick dependency check, base-only method on main, open_first_agent, promotion pick imports missing method, merge-tree clean but broken]
tags: [area/promotion, area/merge-gate, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## The trap

`git merge-tree` / `cherry-pick` clean ≠ runnable on `main`. On #2145 the pick of `0ac4d4a50` applied
without conflict, yet the repaired spec called `AgentsListPage.open_first_agent()` — a method that
exists only on `automation/base` (added by an unrelated 6-case batch, `50e834492`). Merged as-is, the
promotion would have turned the nightly's `Locator.click` red into an `AttributeError` red on the
same card.

## The check (one command, before touching the tree)

```bash
grep -oE "(list_page|agent|detail_page|page_obj)\.[a-z_]+" <spec> | sort -u   # every method the spec calls
git grep -n "def <name>" origin/main -- automation/pages/ automation/utils/    # each one, on MAIN
```
Also every `from utils.X import Y` in the spec. Anything absent on `main` is a **verbatim port** from
`origin/automation/base` (same position, its imports too) — nothing more from that file.

## Ownership

The port is a `pages/**` edit → dispatch a fix-only implementer even when the pick itself is clean.
Ask it to paste `git diff origin/main -- <ported file>` so you can see the diff is exactly the one
method + its import. Then rename to `AI_AQA/fix-…`, gate via `-p devenv`, merge, back-merge.

## Back-merge afterthought

Expect a one-line import-order conflict in the ported file when `main` comes back into `base`
(`import re` above vs below `import logging`). Keep base's line; the resolved file must be
byte-identical to base's pre-merge version — verify with `git diff --quiet HEAD -- <file>`.

Related: [[promotion_gap_card_with_no_main_pr_is_closed_by_your_own_cherry_pick]] ·
[[the_devenv_plugin_is_the_factory_safe_dev_gate]] · [[el6460_breadcrumb_drift_class]]
