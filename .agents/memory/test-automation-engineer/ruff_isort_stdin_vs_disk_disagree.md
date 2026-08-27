---
name: ruff isort disagrees with itself on stdin vs on-disk for automation/tests
description: ruff check <file> flags I001 on automation/tests/** where piping the same bytes via --stdin-filename passes
type: reference
---

Observed 2026-08-27 (ELITEA-1790 / issue #1811), same cwd (`automation/`),
same bytes, `.venv/bin/ruff`:

```
../.venv/bin/ruff check tests/ui/skills/test_agent_max_five_skills_limit.py
  → I001 Import block is un-sorted or un-formatted   (wants the blank line
    between `import pytest` and `from pages... ` REMOVED, i.e. treats
    `pages` as THIRD-party)

cat <same file> | ../.venv/bin/ruff check --stdin-filename <same path> -
  → All checks passed!                               (treats `pages` as
    FIRST-party, blank line correct)
```

So ruff's `src`/first-party detection resolves differently between the two
invocation modes for `automation/tests/**` files importing `pages.*`.

**Consequences:**
- Do NOT use `git show HEAD:<path> | ruff check --stdin-filename …` to decide
  whether a lint error is pre-existing — it silently passes. Write the old
  bytes to a real file **in the same directory** and lint that instead
  (`git show HEAD:<path> > tests/ui/<feature>/zz_lintcheck.py`, lint, `rm`).
- An "on-disk" I001 on one of these files is very likely pre-existing, not
  something the current diff introduced. Confirm before "fixing" it — the
  fix touches import lines, which blows a docs-only scope.
- This is the same class of thing that produced the "module-wide import-block
  sort" noise in ELITEA-1802 / PR #1828.
