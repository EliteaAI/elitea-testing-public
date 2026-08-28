---
name: On a CI-red [Fix] card, check automation/base for an existing fix BEFORE investigating
description: The fix is often already written and merged on base but never promoted to main, which is what CI runs
type: feedback
aliases: [promotion gap, fix already exists, CI red triage, base ahead of main, unpromoted fix]
tags: [area/branching, area/ci, type/trap]
created: 2026-08-28
updated: 2026-08-28
---

## The check — one command, run it FIRST

```bash
git fetch origin
git log --oneline origin/main..origin/automation/base -- <path/to/the/red/test.py>
```

Non-empty output means **the fix may already be written and reviewed**, sitting on
`automation/base`, never promoted to `main` — and `main` is what the nightly
`UI Tests DEV Stable` run executes. The card becomes a *port*, not an
investigation: you inherit an already-reviewed artifact instead of re-deriving it.

## Why this class keeps recurring

The pipeline's normal flow lands test work on `automation/base`. But a test that
was already promoted to `main` now exists in two places, and a `[Fix]` card
raised from a CI failure is reporting the **`main`** copy. Nothing automatically
carries a `base` repair across. So a fix can be "done" for weeks while CI stays
red and re-files the same card under a new number.

Worked case 2026-08-28: #1896 (ELITEA-2051 fork test, `select-option-399`
timeout). The fix was commit `9bb6badd5` / PR #1803, merged to `base` on
2026-08-26 under issue **#1800** — the *same test, same root cause*, still OPEN.
CI never saw it. The whole card was a 4-file port.

**Tell:** a `[Fix]` card whose symptom exactly matches an older OPEN issue on the
same test is a promotion gap until proven otherwise. Search the tracker for the
test name before anything else.

## Porting discipline

`base` is typically hundreds of commits ahead, so **never copy whole files
blindly** — take the test file, then port only the *specific* dependencies it
needs (a `config.py` setting, one API class), and verify each is genuinely
absent from `main` first. Leave everything else behind; unrelated `base` work
riding along in a fix PR is how a repair turns into a regression.

Critically: `main` may hold **newer** versions of shared files (page objects)
than `base`. Copying `base`'s over them reverts other cards' fixes. Diff the
specific methods your test calls; if they are byte-identical, ship no page
object at all.

Related: [[main_and_base_can_carry_different_variants_of_one_spec]] (the reverse
direction — a `main`-only repair overwritten at promotion) ·
[[promoted_test_fixes_branch_from_main]]
