---
name: A [FIX] card's drift can be INVISIBLE on localhost until automation/testids is synced — sync is triage, not housekeeping
description: EliteaUI automation/testids lagged main by 50 commits incl. the very hotfix (EL-6632) that caused the red; an unsynced localhost would have made the pristine control run PASS and mis-classed the card
type: feedback
aliases: [sync before fix triage, localhost lags main, control run passes on stale dev server, EL-6632, credential-status-indicator moved, deliberate drift delivered via main]
tags: [area/triage, area/sync, type/lesson]
created: 2026-09-18
updated: 2026-09-18
---

## What happened (#2349, ELITEA-1183 — card filed as ELITEA-1182)

DEV Stable run #183 went red at `has_credential_status_indicator` on the toolkit detail page. Cause:
EliteaAI/EliteaUI@f73c22f7 (hotfix/EL-6632, merged 21 h before the run) gates the attention icon on
`isInvalid && !isSelected` — it no longer renders on the SELECTED credential, only on the option in the
open dropdown; the row gets `aria-invalid` + a warning underline; the banner keeps icon + tooltip.

`automation/testids` was **50 commits behind `main`** and did NOT carry EL-6632. Had I dispatched before
`sync-base-branches`, the implementer's pristine-`main` control run on localhost would have PASSED
(old UI still served) and the red would have read as "DEV-only / infra" — a Class D mis-triage of a
Class A drift. After the sync the control reproduced the CI red byte-identically.

## The rule
On a `[FIX]` card whose call path touches EliteaUI source, **sync `automation/testids` ← `main` BEFORE
the control run** — and check `git log automation/testids..origin/main -- <component file>` for the
component the failing testid lives in. Delta 3 ("sync first") is triage-load-bearing here, not hygiene.

## Other things this card settled
- **Intake's ELITEA-id comes from `automation_test_id` lists, not from the test's `@allure.issue`
  links.** ELITEA-1182 (moved that morning into `automated-full-regression-ui/toolkits_UI/`) lists all
  three node ids of the file, so the toolkit test was carded under 1182 while its real contract is
  ELITEA-1183. Find the case by `grep -rl "<node id>" ../onetest-ai-tm-Elitea/tests` AND by the test's
  own links; triangulate against the one whose steps the test implements.
- Two of 1182's refs named a non-existent class (`TestToolkitCredentialIndicators.test_agent_…`) —
  Form C that can never correlate. Fixed in the TMS PR; check class names, not just the dotted shape.
- Deliberate-drift delivery shape (a_product_change_is_not_a_product_bug applied): implementer runs
  `adjust-automated-test` on `AI_AQA/fix-…` from `origin/main`, fresh reviewer, my 3× DEV gate via
  `-p devenv`, PR → `main` squash (`Refs`, never `Fixes`), merge `main` into `automation/base`, TMS PR
  with the reworded steps + `automation_pr`, a NON-blocking `question` card for intent. ~2.5 h wall.
- `git merge` on `automation/base` failed with `fatal: stash failed` (autostash + OneDrive); rerun with
  `--no-autostash` — the tree was clean apart from untracked memory files.

Related: [[a_product_change_is_not_a_product_bug]] · [[promoted_test_fixes_branch_from_main]] ·
[[dev_gate_discipline_for_fix_cards]] · [[fix_card_body_can_carry_a_policy_violating_instruction]]
