---
name: On a repair card, run the matched negative control YOURSELF — it converts a green gate into causation
description: Revert only the changed files to origin/main, re-run on the same machine minutes later; expect the card's byte-identical signature. Two commands, and it is the only evidence that the fix is what fixed it.
type: technique
aliases: [negative control, matched control, prove the fix, pristine main control, repair causation, 3x gate is not causation]
tags: [area/gating, area/test-repair, type/technique]
created: 2026-09-09
updated: 2026-09-09
---

## Why the 3× gate is not enough on a REPAIR

A 3×-green gate proves the spec passes *now*. On a repair card it does not prove the **diff** is why —
the environment may simply have recovered, or the failure may have been session-level strain. The
implementer's own before/after pair is a claim; running the control yourself is first-hand evidence,
and it costs one extra invocation.

## The move

```bash
# from the repo root, ON the fix branch, tree otherwise clean
git checkout origin/main -- <each changed file, SPELLED OUT>
grep -c "<a token the fix introduced>" <the changed page object>     # 0 = genuinely pristine
cd automation && AUTOMATION_DIR=$PWD DEV_ELITEA_URL=https://dev.elitea.ai DEV_APP_PREFIX=/app \
  PYTHONPATH=/tmp/devenv_harness HEADLESS=true ../.venv/bin/pytest -p devenv -p no:cacheprovider \
  -v --reruns=0 "<node-id>" "<node-id>"
cd .. && git checkout HEAD -- <the same files>                        # restore
git status --short                                                    # must be clean
```

Then grep the control log for the **card's own signature**, not just for "failed". Matching the exact
string (here `subtree intercepts pointer events` + the same `css-…` hash) is what makes it a matched
control rather than "it also broke somehow".

Worked case 2026-09-09, #2052: branch 3× `5 passed` (144/155/151 s) vs pristine `origin/main`
`2 failed in 70.54s` with the byte-identical nightly signature, same machine, minutes apart.

## The trap that ate the first attempt — zsh does not word-split

```bash
F="a.py b.py c.py"
git checkout origin/main -- $F      # ✗ ONE pathspec "a.py b.py c.py" → error, NOTHING reverted
```
The checkout errors, and if you don't read the output you run the "control" **against the fixed code**
and get a meaningless PASS that looks like a disproof. Spell the paths out, or use an array. Always
assert the revert landed (`git status --short` count, plus the token grep above) before running.

Same family as [[zsh_unquoted_var_no_word_split]]; here the failure mode is worse, because the
command that failed is not the command whose output you were reading.

## Restore, then verify the restore

`git checkout HEAD -- <files>` and a clean `git status` — never leave the control state behind on a
shared clone. Untracked files from other roles are NOT yours to clean.

Related: [[fix_card_may_already_be_fixed_by_a_sibling_pr]] (the same control pointed the other way) ·
[[dev_repro_use_localhost_not_shared_env_test]] · [[promoted_test_fixes_branch_from_main]]
