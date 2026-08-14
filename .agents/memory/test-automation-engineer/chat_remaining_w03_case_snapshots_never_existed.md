---
name: chat-remaining-w03 case snapshots never existed
description: chat-remaining-w03 dispatches always name .agents/automation/chat-remaining-w03/cases/<ID>.md but that dir never existed for this campaign
type: project
---

Every combined analyst+implementer dispatch on the `chat-remaining-w03` batch
(ELITEA-2105-2109, 2110/2112/2113, 2111 — 4 dispatches in a row) named a case
snapshot at `.agents/automation/chat-remaining-w03/cases/<ID>.md` that never
existed on disk (the `cases/` subdir was never created for this campaign at
all — confirmed via `ls .agents/automation/` listing dozens of other
campaigns' `cases/` dirs but none for `chat-remaining-w03`).

**Don't loop on this or treat it as "digest missing → needs-analyst".** It's
an intake-tooling gap for this one campaign, not a signal the ground is
novel. Go straight to the real TMS case file instead — either:
- `../onetest-ai-tm-Elitea/tests/automated-full-regression-ui/chat/ELITEA-<id>_<slug>.md`
  (read directly, fast), or
- `mcp__onetest-tms__get_test_case` (used successfully in an earlier w02
  dispatch when even the raw file path was unknown).

The `test-specs/chat-interface/_surface.md` exploration digest IS present and
current for this feature area — that's the real "is the ground mapped"
signal for chat-interface, independent of the missing per-case snapshot.
