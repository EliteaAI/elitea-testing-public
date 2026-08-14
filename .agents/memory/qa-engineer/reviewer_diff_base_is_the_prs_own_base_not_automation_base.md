---
name: Reviewer diff base is the PR's own base, not automation/base
description: gh pr view --json baseRefName first — a case PR's base is often a batch trunk (tests/batch-<slug>), not automation/base; diffing automation/base silently widens the diff to every case already merged onto that trunk
type: feedback
---

## What happened (ELITEA-2093 review, PR #1509, 2026-08-14)

Dispatch named the branch (`tests/ELITEA-2093-agent-hub-conversation-starter`)
but not the PR's actual base. Diffing `origin/automation/base...HEAD` picked
up **16 files across 2 cases** (ELITEA-2093 AND the already-merged ELITEA-2091
sibling, both landed on the shared batch trunk `tests/batch-chat-remaining-w01`
before this case's branch was cut) — a materially wrong review scope: it would
have made me triangulate ELITEA-2091's files against ELITEA-2093's AFS/case,
and could have flagged ELITEA-2091's own diff as "not part of this PR" noise
or, worse, silently absorbed it into this review's verdict.

`gh pr view <N> --json baseRefName,files` gives the real base AND the real
file list in one call — diff against THAT ref (`git diff
origin/<baseRefName>...origin/<headRefName>`) and cross-check the resulting
file list matches `--json files` exactly before triangulating anything.

## Why it happens

The batch pipeline cuts each case's branch from the **batch trunk**, not from
`automation/base` — the trunk already carries every case merged earlier in the
same batch. `automation/base` is only the trunk's own eventual target, several
merges behind mid-batch. This is the reviewer-side mirror of the implementer's
own `mechanical_greps_diff_against_batch_trunk_not_origin_base.md` gotcha —
same root cause, different slot.

## Rule

Before the first diff of any PR review: `gh pr view <N> --json
baseRefName,files`. Never assume `automation/base` (or any other seeded
default base) is the PR's actual base — ask the PR.
