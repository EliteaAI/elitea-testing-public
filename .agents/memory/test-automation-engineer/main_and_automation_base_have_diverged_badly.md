---
name: origin/main is NOT a superset of automation/base — check before any main-targeted work
description: main still carries a planted assert False and cannot collect tests/unit; fixes merged to automation/base never reach it
type: project
aliases: [main vs automation/base, intentional failure smoke test, tests/unit collection error, main divergence]
tags: [area/branching, status/open]
created: 2026-09-07
updated: 2026-09-07
---

## What bit me (2026-09-07, issue #2023 / PR #2025)

Dispatched to fix a CI failure **on `main`** (issue #2023's Fix Branch Strategy targets `main`,
not the usual `automation/base`). Two things on `main` are broken and are NOT on
`automation/base`:

1. **A planted failure is still live.** `tests/ui/smoke/test_ui_smoke.py::TestHomePage::test_page_loads`
   ends in `assert False, "INTENTIONAL FAILURE: Testing webhook pipeline integration"`, from
   commit `30c2d1e08`. It was removed on `automation/base` by PR #2017 — **that removal never
   reached `main`.** The DEV `smoke` job stays red regardless of any other fix.
2. **`pytest tests/unit` does not collect on `main`** — 3 collection errors
   (`test_actions.py`, `test_agent_hub_like_cleanup_soft_failures.py`,
   `test_pipeline_state_panel_priority_markers.py`) importing `tests.ui.*` modules that exist
   only on `automation/base`. Run a new unit gate **by file selection**, not `tests/unit`.

Also: `ruff check .` finds **708** errors on `main`. "Ruff clean" is unachievable there —
scope ruff to the changed files and prove the rest pre-existing with a pristine control.

## The move

Before any `main`-targeted work, diff the two branches for the files you touch and **run a
pristine-`origin/main` control** for anything red. On this task the control returned
byte-identical failures (same tests, same messages, same x-positions) and converted "did my
diff break it?" into evidence in ~80 s. Cheap; do it every time.

Related: [[verify_your_own_delivery_before_handoff]]
