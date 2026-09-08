---
name: Ruff repo baseline is dirty — judge "ruff clean" as a delta, not an absolute
description: `ruff check .` reports ~743 pre-existing errors repo-wide; prove your diff adds none
type: project
---

`../.venv/bin/ruff check .` from `automation/` (the command `.agents/conventions.md` names) does
**not** exit 0 on this repo and has not for a long time — measured 2026-09-09: **743 errors**,
337 auto-fixable. They are spread across `api/`, `pages/`, `tests/`; `pages/agent_detail_page.py`
alone carries 6 (I001, two F401, UP008, F541, E501).

So a dispatch asking for "ruff clean" cannot mean a clean whole-repo run. What it can mean, and
what to actually verify:

```bash
# baseline for a file you touched
git show origin/main:automation/tests/ui/x/test_y.py > /tmp/base.py
cd automation && ../.venv/bin/ruff check --no-cache /tmp/base.py     # findings BEFORE
../.venv/bin/ruff check tests/ui/x/test_y.py                          # findings AFTER
```

Same findings before and after ⇒ your diff introduced none. Say exactly that in the Run Report
(with both outputs) rather than claiming "ruff clean", which would be false.

**Do not "fix" the baseline as a side effect** — the I001 hits in particular come from
`pyproject.toml`'s `[tool.ruff]` having no `src`/`known-first-party` setting, so `config`,
`pages`, `utils` are classified third-party and ruff wants a different import grouping than the
whole suite uses. Re-sorting one file's imports to satisfy it makes that file inconsistent with
its ~230 neighbours. It is a suite-wide config decision for the lead, not a repair-PR change.

Companion entry: `ruff_isort_stdin_vs_disk_disagree.md` (why a stdin-piped ruff run can read clean
when the on-disk file is not).
