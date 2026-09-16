---
name: A clean cherry-pick to main can still be broken — hidden symbol dependency on an unpromoted sibling repair
description: Git auto-merging a page object cleanly proves nothing about the SYMBOLS the picked method bodies reference; run the spec once locally before gating, or grep every `self.<field>` against main. Fix = promote the whole sibling commit, never hand-patch the field.
type: feedback
created: 2026-09-16
tags: [area/promotion, area/git, area/promotion-gap]
---

## What happened (#2330, ELITEA-2022, PR #2334)

Cherry-picked `09219bb8f` (the #2139 repair) onto a branch cut from `main`.
The spec / AFS / `_surface.md` conflicted (expected, dispatched fix-only);
`pipelines_list_page.py` **auto-merged cleanly**. First local run:
`AttributeError: 'PipelinesListPage' object has no attribute 'empty_state_title'`
— the pick's new `wait_for_pipeline_absent()` reads a class field that only
`6855dc3f4` (ELITEA-2024 / #2118, also unpromoted, also `Ready`) defines. The
pick's hunks never touch the field's region, so the merge had nothing to flag.

## Rules

1. **A clean merge is a textual fact, not a dependency proof.** Before gating a
   cherry-pick to `main`, either run the spec once locally (cheapest, 12 s) or
   grep every `self.<field>` / helper the picked method bodies reference:
   `git log origin/main..origin/automation/base -S'<field>' -- <page object>`.
   A hit on a sibling commit = a hidden dependency.
2. **Promote the whole sibling commit, never the one field.** Hand-patching the
   field in is a silent partial promotion of another card (its AFS, its test
   changes stay behind, and the field's origin becomes untraceable). Pick the
   sibling with `-x` FIRST-or-after (order does not matter if it applies clean),
   drop `.agents/memory/**` from it, gate BOTH promoted node ids together on DEV,
   and back-link the sibling card ("promoted as a dependency — found while
   working #N"). Scope rule ("only this issue") does not forbid it: the
   dependency is required to deliver this card, and the sibling is already
   reviewed + gated + `Ready`.
3. **The engineer's Run Report is the trigger** — the fix-only dispatch runs the
   spec once after `--continue`; make that step non-optional in the prompt.

Cost of missing it: a 3× DEV gate thrown away plus a session. Cost of the check:
one local invocation.
