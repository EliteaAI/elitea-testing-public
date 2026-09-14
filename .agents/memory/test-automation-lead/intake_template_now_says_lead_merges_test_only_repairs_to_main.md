---
name: The [FIX] intake template (da663ef, 2026-09-14) says the lead merges test-only repairs to main — act on it, flag the seed conflict once
description: A human answered #1938 §1 by rewriting the intake routine; a test-only, already-gated repair PR to main is now merged by the lead after its own 3× DEV gate — the seed's "never PR main" line is stale, not authoritative, for [FIX] repairs
type: feedback
aliases: [AI_AQA template, auto-merge if test-only, PR to main for FIX cards, da663ef, promotion gap closed by merging]
tags: [area/triage, area/merge-gate, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## What changed (#2286, ELITEA-1899, re-detection 16 of 16)

`automation/routines/test_failure_intake.yml` @ `da663ef` (Aliaksei Breilian, 2026-09-14 20:08 Z)
rewrote every [FIX] card's Instructions: branch from `main` (`AI_AQA/fix-<test>`), `AI_AQA:` commit
prefix, **PR to `main`**, **"Auto-merge if test-only (no backend/UI changes required)"** via
`gh pr merge --squash`. That is a human answering open question #1938 §1 *by action* — and it matches
the practice already on record (#1937, #1923–#1931, #2012, #2133 all merged to `main` by the lead).

Fifteen prior ELITEA-1899 cards ended `duplicate` + "human merges #2056". Under the new template the
correct disposition of a promotion-gap [FIX] card whose repair PR to `main` already exists is:
**gate the merge candidate on DEV 3× (§ Merge gate, before `gh pr merge`), squash-merge with an
`AI_AQA:` title, merge `main` back into `automation/base`, close.** Not another no-op.

## Guard rails that still apply

- **Never `--body 'Fixes #<issue>'`** (the template's step 5): it auto-closes the card on merge, and
  `Done`/close are human-only. Use `Refs #…`.
- **Instruction 7 (regular locators)** is still the inverse of the testid-only policy — override it
  explicitly every time (#2071 / #2096).
- **"Test-only" was read as "the fix needs no product change", not "the test goes green"** — so a
  sanctioned-RED repair qualifies. Declared on #1938; if a human narrows it, stop merging those.
- The seed (`.agents/profile.md` § Automation PR policy: "never PR `main`") is now contradicted by
  the template. Flagged ONCE on #1938 — do not re-file a question; do not park the next card on it.
- Merging to `main` fires CodeQL `Analyze` — unavoidable; not a "triggered workflow" in the
  template's sense (no UI-test run dispatched).

## Mechanics that worked

- Merge candidate = `git checkout -b tmp/gate-<pr> <pr-head> && git merge origin/main` (after
  `merge-tree --write-tree` says clean); gate it with the `-p devenv` plugin
  ([[the_devenv_plugin_is_the_factory_safe_dev_gate]]); delete the temp branch; return to
  `automation/base` BEFORE `gh pr merge`.
- The main → base sync afterwards conflicts on the same append-only agent-memory logs every time
  (the squash re-introduces union-merged text). Resolve with `git merge-file --union` per file, then
  dedupe any index line it doubles (`sort | uniq -d`) — mechanical, no authored content.
- Squash means base carries both the original commits and the squash; `origin/main...automation/base`
  still reads `0 / N` afterwards, which is the invariant that matters.

Related: [[a_human_hotfix_on_main_can_half_execute_an_open_question]] ·
[[fix_card_body_can_carry_a_policy_violating_instruction]] ·
[[ancestry_check_is_the_first_move_on_a_fix_card]]
