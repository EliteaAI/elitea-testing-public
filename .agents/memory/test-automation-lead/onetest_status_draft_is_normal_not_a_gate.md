---
name: onetest status draft is normal, not a not-actionable gate
description: this project's TMS status:draft means "not yet automated" (the intake target), not "author marked not-actionable" — the generic playbook example doesn't apply here
type: feedback
---

The orchestration playbook's § Session-start preflight lists "Draft" as an example
of an author-marked not-actionable status to skip. **That generic example does NOT
apply to this project's onetest TMS.**

Evidence, cross-checked on ELITEA-1933 (issue #123, 2026-07-17):

- `.agents/test-automation.yaml` § `intake.selector` literally targets
  `status: draft` as the population THIS PIPELINE automates — draft is the intake
  target, not an exclusion.
- `.agents/test-automation.yaml` § `already_automated_when` requires
  `status: ready` AND `execution_type: automated` AND non-empty `automation_test_id`
  — i.e. `status: ready` is the **post-automation** state.
- Confirmed empirically on ELITEA-1737 and ELITEA-1922 (both already automated,
  PRs merged): both carry `status: ready`, `execution_type: automated`, a
  populated `automation_test_id`/`automation_pr`.

So for onetest cases in `onetest-ai-tm-Elitea`: `status: draft` + `execution_type:
manual` = normal pre-automation state (proceed to analyst execution). `status:
ready` + `execution_type: automated` + populated `automation_test_id` =
already covered (route as `already-covered`, don't re-automate).

**There is no author-gate on `draft` here** — nearly every case in the repo is
`draft` until this pipeline automates it. An analyst or orchestrator that applies
the generic "skip Draft cases" instinct will misroute almost every dispatch.

If a genuinely un-actionable case ever appears in this TMS, it will need a
different signal than `status` (check tags / an explicit note in the case body) —
don't reach for `status: draft` as that signal.
