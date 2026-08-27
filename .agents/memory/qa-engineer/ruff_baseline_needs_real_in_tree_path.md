---
name: Ruff lint baselines need a real in-tree path, not --stdin-filename
description: Comparing a PR's ruff output against the base branch via --stdin-filename mis-attributes I001 as new; write the base version to a temp file in the SAME directory instead
type: feedback
aliases: [ruff baseline, is this lint error new, I001 false positive, stdin-filename ruff]
tags: [area/review, type/gotcha]
created: 2026-08-22
updated: 2026-08-28
---

## The trap

Static review (no checkout allowed) tempts you to baseline lint like this:

```bash
git show <base>:automation/pages/x.py | ../.venv/bin/ruff check --stdin-filename pages/x.py -
```

Ruff's isort (`I001`) resolves first-party vs third-party from the file's real
location on disk / `src` detection. Through stdin it resolves differently, so a
file that reports `I001` when checked as a real path reports **All checks passed**
through stdin. Result: a pre-existing `I001` looks like the PR introduced it.

Field case: ELITEA-1964 review (PR #1667). `credentials_list_page.py:16 I001`
was flagged as "new" by the stdin baseline; a real-path baseline showed it was
already on the trunk. Only `credential_detail_page.py:40` and the new spec were
genuinely new.

## Do this instead

```bash
cd automation
git show <base>:automation/pages/x.py > pages/_tmp_base_x.py
../.venv/bin/ruff check --output-format=concise pages/_tmp_base_x.py
rm -f pages/_tmp_base_x.py
```

Same directory as the original (so `src` detection matches), `--output-format=concise`
so rule codes are visible — the default output shows only `-->` locations.

## Same trap, second shape: a /tmp mirror directory

A `/tmp/<mirror>/` tree assembled from `git show <branch>:...` has the same defect
for the same reason. Ruff infers first-party packages from what exists **next to**
the file, so a mirror containing `pages/` but not `config.py` / `utils/` classifies
`pages` first-party and `config`/`utils` third-party — 4 bogus `I001`s across four
specs whose real-path run is `All checks passed`. Verified 2026-08-28 (settings-w05
secrets review, PR #1904).

Cheapest correct move when the shared tree is **already on the branch under review**
(the serial batch pipeline usually leaves it there — check `git rev-parse
--abbrev-ref HEAD` first): just `cd automation && ../.venv/bin/ruff check <paths>`
on the real files. No mirror, no stdin, no checkout.

Related: [[reviewer_mechanical_greps_must_run_from_repo_root]]
