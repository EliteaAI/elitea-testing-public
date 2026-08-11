---
name: git diff <ref>... (triple-dot, no second ref) silently drops uncommitted changes
description: When HEAD == <ref> (branch just cut, no commits yet), `git diff <ref>...` diffs commit-to-commit (merge-base..HEAD) and shows ZERO lines even with staged/unstaged edits — the mechanical self-check grep then falsely reports "0 hits" instead of catching a real violation. Use `git diff <ref> -- path` (two-dot/direct form) to include the working tree.
type: feedback
---

## What happened (ELITEA-2362, implementer, 2026-08-11)

Ran the mandatory pre-handoff mechanical grep exactly as written in the dispatch:
`git diff origin/automation/base... -- automation/ | grep -nE '...'`. The branch
`tests/2362-agent-chip` had just been cut from `origin/automation/base` with no
commits of its own yet — only staged/unstaged working-tree edits. The command
returned **0 lines**, including 0 lines of `git diff --stat` — a silent, total
miss, not just an empty grep result. A real hit existed
(`self.switch_participant_button.locator(self.CHAT_SWITCH_PARTICIPANT_AVATAR)`,
a compliant one, but the check needed to actually SEE it to classify it).

## Root cause

`git diff A...` (trailing dots, no second ref) is `git diff $(git merge-base A HEAD) HEAD`
— a **commit-to-commit** comparison. When `HEAD` IS `A` (no divergent commits yet),
`merge-base(A, HEAD) == HEAD == A`, so the diff is comparing a commit to itself:
always empty, regardless of how much uncommitted work sits in the working tree.

`git diff A` (no trailing dots) is direct: commit `A` vs the **working tree**
(staged + unstaged), which is what a pre-commit self-check actually needs.

## The fix

Before trusting a "0 hits" result from any mechanical grep, sanity-check with
`git diff <ref> --stat -- <path>` (two-dot form) first — if that's also empty,
0 hits is real; if it shows changed files, redo the grep with the two-dot form:

```bash
git diff origin/automation/base -- automation/ | grep -nE '^[+].*(get_by_role|...)'
```

Reserve the triple-dot form for comparing two commits that have ALREADY diverged
(e.g. reviewing a merged PR's history, or a batch trunk with its own commits ahead
of base) — not for a self-check on a branch that may still be commit-for-commit
identical to its base.

This is a distinct trap from `mechanical_greps_diff_against_batch_trunk_not_origin_base.md`
(wrong REF entirely, inside a live batch) — this one is about the triple-dot SYNTAX
producing a false-empty result even against the *correct* ref, whenever HEAD hasn't
diverged from it yet (any single-case dispatch cutting a fresh branch, not just batches).
