---
name: On a CI-red [Fix] card, check automation/base for an existing fix BEFORE investigating
description: The fix is often already written and merged on base but never promoted to main, which is what CI runs
type: feedback
aliases: [promotion gap, fix already exists, CI red triage, base ahead of main, unpromoted fix]
tags: [area/branching, area/ci, type/trap]
created: 2026-08-28
updated: 2026-09-09
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

## Check for a staged promotion BEFORE assuming you must port

The port is the *expensive* outcome. Check for the cheap one first — the
promotion may already be open and merely unmerged:

```bash
env -u GITHUB_TOKEN gh pr list --repo <repo> --state all --search "<CASE-ID>" \
  --json number,title,state,baseRefName,mergeCommit
```

An **OPEN PR with `base=main`** means the repair is already staged and is waiting
on a *human merge* — there is nothing to build, port, or review. Verify the PR
head's copy of the test is byte-identical to `automation/base`
(`diff <(git show origin/<head>:<path>) <(git show origin/automation/base:<path>)`),
then report the gap and stop. Do not open a second PR.

Worked case 2026-09-09: #2081 (`[FIX][ELITEA-1899]`, agent icon) — the repair was
merged to `base` **and** PR #2056 to `main` was already open from the previous
card, #2051. The nightly kept re-filing because #2056 had not merged. Zero code
changed; the whole card was verification + a closure record.

**Corollary — the duplicate chain is the tell.** A `[FIX]` card that is the
*second* one for the same test (same assertion, different run id) is almost never
new work. Find the first card, read its closure record, and check whether what it
promised has actually landed.

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

## Third worked case, 2026-09-09: #2114 (ELITEA-2448) — nothing staged at all

`git log --oneline origin/main..origin/automation/base -- <spec>` returned the
repair commit `3f26bef61` (PR #2091), merged to `base` at 11:41Z the same day.
`main` still held the pre-repair `wait_for_embedded_chat_response()` + hard
`expect(run_node_label).to_be_visible()` — and that assert's message is
*verbatim* the CI failure string, which is the single strongest one-command proof
of an unpromoted repair.

Unlike #2081 (staged promotion PR #2056 awaiting a human merge), here the "cheap
outcome" check came back empty: no open PR had base `main`. So the escalation
ladder has three rungs, not two — **(1) already promoted → nothing to do ·
(2) promotion PR open → report, do not open a second · (3) nothing staged →
report the gap, name the human, still do not open it.**
