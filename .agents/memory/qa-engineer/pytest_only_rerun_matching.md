---
name: pytest --only-rerun matching
description: What pytest-rerunfailures' --only-rerun actually matches, so you can tell statically whether a failure shape gets auto-rerun (masked in junit) or stays a visible red
type: reference
aliases: [only-rerun, reruns, auto-rerun, rerunfailures, soft assert rerun]
tags: [area/framework, type/reference]
created: 2026-09-18
updated: 2026-09-18
---

## The rule (verified in-venv 2026-09-18, pytest-rerunfailures `_try_match_error`)

`--only-rerun <regex>` is matched with `re.search` against the string
`f"{excinfo.type.__name__}: {excinfo.value}"` — the exception CLASS NAME plus
`str(value)`, NOT the traceback and NOT `longrepr`.

Consequences for judging a repair's rerun semantics (`automation/pytest.ini`
lists `TimeoutError`, `502/503/504`, `Connection refused/reset`, `net::ERR_ABORTED`,
`Failed to load resource`, `404 ()`, `WebSocket`):

- A raw `playwright._impl._errors.TimeoutError` (e.g. `Locator.wait_for`) →
  type name is `TimeoutError` → **auto-rerun**, junit records PASS if the rerun
  passes. This is how an intermittent product defect hides for weeks
  (ELITEA-2056/#2366: the pre-repair `.node` wait was absorbed by `--reruns=2`).
- A Playwright `expect(...)`/`expect.soft(...)` timeout → `AssertionError` whose
  message reads `Timeout 10000ms exceeded` (no literal `TimeoutError`) → **never
  rerun**. An `ExceptionGroup` from the soft scope → `str()` is
  `multiple assertion failures (N sub-exceptions)` → never rerun either.
- So converting a raw wait into a retrying `expect` does not just improve the
  message — it flips the failure from "absorbed by reruns" to "visible red".
  A repair that does this must say so (the ELITEA-2056 AFS § Adjustment does).

Related: [[project_briefing]] · `.agents/testing.md` § Merge gate (`expect.soft`
failures ARE reds).
