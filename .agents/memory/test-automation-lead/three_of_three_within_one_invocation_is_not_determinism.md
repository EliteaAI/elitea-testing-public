---
name: 3/3 failures inside ONE pytest invocation is not the same evidence as 3/3 across invocations
description: --reruns=2 makes a single transient look deterministic, which is exactly the input the sanctioned-RED and root-cause decisions key on
type: feedback
aliases: [reruns look deterministic, 3 of 3 same invocation, rerun evidence, deterministic failure evidence, one invocation three attempts]
tags: [area/gate, area/triage, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

`pytest.ini` carries `--reruns=2`, so one invocation produces up to three attempts. When all
three fail, the tail reads like a deterministic failure — and "deterministic, 3/3" is the
exact phrase § Merge gate's sanctioned-RED exception and every root-cause verdict key on.

But the three attempts share one process, one browser context, one backend moment and one
accumulated account state. A stuck menu, a cold route chunk or a stale conversation persists
across all three. That is **one** observation, not three.

Worked case (#2142 / ELITEA-1793, analyst session): localhost invocation 1 failed **3/3** at
Step 2 on a plus-menu Agents submenu stuck at `Loading...`. Invocation 2 passed **7/7** clean,
`reruns.json == {}`. Had invocation 1 been read as the signature, the card would have been
routed to the wrong subsystem entirely.

## The rule

Determinism claims need **separate invocations** — which is already why § Merge gate spells out
"three SEPARATE consecutive pytest invocations of the SAME spec", not one invocation with three
passing tests. Apply the same standard when reading a *failure*:

- Same signature across ≥2 fresh invocations ⇒ treat as deterministic.
- 3/3 inside one invocation ⇒ one datapoint. Run it again before believing it.
- Read attempt **causes** from `reports/allure-results/*-result.json` (grep by `fullName`,
  read `statusDetails.message`), never invocation exit codes — and check `reports/reruns.json`,
  which is the cheapest tell that an apparently clean invocation was not.

CI is the exception that proves the point: its 3 retries are also one invocation, so a CI
"failed all 3 retry attempts" line is likewise one observation — reproduce locally before
believing any red of that shape.

Related: [[dev_only_locator_red_can_be_an_overwritten_promoted_testid]] · [[gate_on_the_environment_the_repair_is_FOR]]
