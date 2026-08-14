---
name: onetest index.json drifts stale — needs a periodic rebuild independent of any batch
description: index.json isn't CI-rebuilt; a full rebuild during approved-top10 picked up 2726->2743 cases unrelated to that batch
type: project
---

Rebuilding `onetest-ai-tm-Elitea/index.json` after the `approved-top10`
TMS back-write (via `onetest-tms/scripts/_index.py --dir tests --out
index.json`) picked up **2726 → 2743 cases** — far more than the 10 this
batch touched. `git diff --stat` on the rebuild showed thousands of
unrelated line changes, including cases (e.g. a `settings` module batch,
`ELITEA-2242`/`2243`) that existed as `.md` files but were never reflected
in the index at all before this rebuild.

Per `test-automation.yaml`'s own note, "`build-index` CI is a stub" — nothing
auto-rebuilds this file, so it silently drifts every time a case file is
added or edited without someone remembering to rebuild. A stale index means
`onetest-tms`'s `correlate_results`/`automation_coverage` verbs are reading
wrong data for cases well outside whatever batch happens to trigger the next
rebuild.

Worth flagging to the human / to scout as a standing maintenance gap: a
periodic (e.g. weekly) rebuild-and-commit sweep of `index.json`, independent
of any specific automation batch, would keep coverage reporting honest. Not
something this role should silently patch over every time it happens to
touch the TMS repo — it's a process gap, not a per-batch task.
