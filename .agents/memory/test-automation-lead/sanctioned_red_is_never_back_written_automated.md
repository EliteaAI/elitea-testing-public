---
name: A sanctioned-RED case is never back-written execution_type-automated
description: the spec merged, but the case did NOT deliver coverage — back-writing it ready/automated is a hidden green; re-check PRIOR waves whenever this rule surfaces
type: feedback
created: 2026-08-28
updated: 2026-08-28
---

## The rule

`.agents/testing.md` § Merge gate, verbatim: a spec carrying `expect.soft()` /
soft-failure aggregation + `# Known defect: #N` **is** sanctioned-RED, and

> its case stays `blocked-on-#N`, **never** `automated`.

An `expect.soft()` failure IS a pytest failure (pytest-playwright re-raises the
collected soft errors at the end of `pytest_runtest_call`). The spec is merged and
useful — it will flip green the day the product ships the fix — but the CASE has not
been verified, so `execution_type: automated` + `status: ready` is a **false coverage
claim**, and `automation_coverage` counts it.

## What I actually got wrong (2026-08-28, backlog #1398)

I applied the rule correctly *within* wave 5 (9 sanctioned-RED cases, none back-written),
and only then thought to re-check earlier waves. I had broken it three times:

| Case | Wave | Ticket | Wrongly written |
|---|---|---|---|
| ELITEA-2243 | w01 | #1771 | `ready` / `automated` |
| ELITEA-2289 | w04 | #1884 | `ready` / `automated` |
| ELITEA-2291 | w04 | #1885 | `ready` / `automated` |

Corrected to `draft` / `manual` + a `sanctioned_red: "<ticket>"` field. The card's
delivered count fell **36 → 33**.

## The correct shape

Keep `automation_test_id` — the spec exists and CI correlation should still link it.
Revert only the pair that CLAIMS coverage:

```yaml
status: draft            # not ready
execution_type: manual   # not automated
automation_test_id:      # KEEP — correlation key, the test is real
  - tests.ui.<...>
sanctioned_red: "#1884"  # why it is not automated
```

`.agents/test-automation.yaml` § `already_automated_when` requires **all three**
(`automated` + `ready` + non-empty id), so keeping the id while reverting the other two
is exactly right: linked, not counted.

## The habit this needs

**The rule is easy to obey inside one wave and easy to forget across waves.** Each wave
I judged the current batch correctly and never looked back. So:

> Whenever this rule comes up in a wave, immediately re-check every PRIOR wave of the
> same card for cases you back-wrote before the rule was front-of-mind.

Cheap sweep, per area folder in the TMS clone:

```bash
grep -l 'execution_type: automated' tests/automated-full-regression-ui/<area>/*.md \
  | xargs grep -L 'sanctioned_red:' \
  | xargs -I{} sh -c 'grep -q "status: ready" {} && echo {}'
```
…then cross-check each hit's spec for `# Known defect:` / `soft_failures`.

**A smaller honest number beats a larger false one** — and the closure record must say
the count moved and why, or the correction is invisible.

Related: [[workflow_gate_verdict_is_not_the_merge_gate]] · [[already_covered_tms_backwrite_needs_covering_test_health_check]] · [[settings_area_backlog_1398]]
