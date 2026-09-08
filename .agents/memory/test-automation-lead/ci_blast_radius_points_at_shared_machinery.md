---
name: A whole-matrix CI red points at shared machinery, not the named commit
description: N/N jobs red across unrelated features = one shared conftest/page-object cause; triage by common stack frame, not by the commit
type: feedback
---

When *every* job of a CI matrix goes red across unrelated feature areas, the named
commit on the card is almost never the cause — the arithmetic is against it. A
chat-scoped change cannot redden pipelines, admin, toolkits, skills and artifacts.

**Triage move: find the common stack FRAME, not the common test.** Pull 3–4 job logs,
extract one full traceback each, and look for the frame they share. It will be in
`conftest.py`, a `BasePage` method, or a fixture — the machinery every suite routes
through.

Field case 2026-09-07 (#2023): 10/10 DEV Stable jobs red. Shared frame was an autouse
fixture monkey-patching `page.goto` into an unguarded `page.evaluate`. One helper, one
fix, whole matrix restored. The auto-triage had labelled it "infrastructure (HIGH)" —
right that it was not the commit, wrong that it was the environment, and that guess
would have sent someone to check DEV health for hours.

**The duration tell is the cheapest signal available, and it works before you read a
single log.** Jobs that die in 100–160 s when they normally run 15–20 min did not run
and fail — they *aborted at the first navigation*. Compare the failing run's job
durations against a healthy run's before anything else; a 10× drop means shared setup,
and a 10× recovery after a fix is the proof it worked.

Corollary: fixing shared machinery **unmasks** the ordinary failures it had been
hiding. Expect a handful of unrelated reds to appear afterwards (8, in #2023's case).
That is the fix working, not the fix failing — say so explicitly in the closure record
so nobody reads it as a regression.
