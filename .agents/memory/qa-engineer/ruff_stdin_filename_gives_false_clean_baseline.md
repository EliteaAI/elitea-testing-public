---
name: ruff --stdin-filename gives a FALSE "clean" baseline in review
description: Proving a lint error is pre-existing needs the base file copied in place with --no-cache; --stdin-filename reports "All checks passed" for a file that fails on disk
type: feedback
aliases: [ruff baseline, pre-existing lint, stdin-filename, lint control run]
tags: [area/review, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

## The trap

Reviewing a branch, `ruff check` flagged 2 errors in `automation/config.py`
(`I001` import block un-sorted, `UP045` `Optional[int]`). Before blocking, I ran the
obvious control — the base version of the same file through stdin:

```bash
git show <base>:automation/config.py > /tmp/base_config.py
../.venv/bin/ruff check --output-format=concise --stdin-filename config.py - < /tmp/base_config.py
#  -> "All checks passed!"      <-- WRONG
```

That reads as "the branch introduced both errors" and would have produced a false
blocker. The errors are **pre-existing on base** — the branch never touched the
import block, and `Optional[int]` is on an unmodified line.

## The reliable control

Copy the base file **in place** (same path, so config discovery and per-file
settings resolve identically) and run with `--no-cache`, then restore:

```bash
cp config.py /tmp/branch_backup.py
cp /tmp/base_config.py config.py
../.venv/bin/ruff check --no-cache --output-format=concise config.py    # -> the SAME 2 errors
cp /tmp/branch_backup.py config.py
git status --porcelain config.py                                        # must print nothing
```

Restore-and-verify is not optional: the reviewer slot is static, and leaving a
modified working file behind on a shared tree is the damage this control was meant
to avoid.

## The general rule

**A "did this branch introduce it?" control run must exercise the same code path as
the failing run.** Alternate input channels (stdin, a temp path, a different cwd)
silently change tool configuration resolution, and the difference shows up as a
clean baseline rather than an error — the failure mode that manufactures blockers.

Related: [[elitea_roles_are_project_scoped]]
