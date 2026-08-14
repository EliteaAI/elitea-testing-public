---
name: Stray uncommitted AFS from an interrupted prior run
description: An untracked but complete AFS on disk at dispatch start is real work — verify claims, don't discard or blind-trust
type: feedback
---

Confirmed live 2026-08-04 (ELITEA-2042 analyst dispatch). On arrival, the batch
trunk already had `test-specs/pipelines/l2_pipeline-state-panel-...ELITEA-2042.md`
fully written (12 steps, Coverage Map, handles, defect filed) but **untracked** —
a prior analyst session had done the work and got interrupted before the
mandatory commit step. `git log` on the file showed nothing.

**What to do:** don't discard it (it's real analyst labor) and don't blind-commit
it either (an interrupted session may have written claims it never actually
finished, e.g. "I updated `_surface.md`" when it hadn't). Spot-check the
load-bearing claims before trusting:
- Any filed tracker issue (`gh issue view <n>`) — does it exist and match the
  described defect?
- Any testid claimed present on `automation/testids`/`main` — fresh
  `git fetch origin` + `git grep` per role-overrides discipline.
- Any "already wired in the page object" claim — grep the page object file.
- Any "updated `_surface.md`" claim — grep for the described section; if
  missing (as it was here), write it yourself before committing — the AFS's
  own text is now the citation you're fulfilling, not just prose.

Only after the above checks passed did this session commit the file as its own
output. Treat a stray uncommitted AFS as a lead, not a fact.
