---
name: A review finding names ONE instance — sweep the siblings before handing back
description: Fixing only the reported chart/preset/card buys another review round; the same weakness is usually replicated across the unit.
aliases: [sibling sweep, fix round, review round, same weakness elsewhere]
tags: [type/process, area/review]
type: feedback
created: 2026-08-28
updated: 2026-08-29
---

## The pattern that costs rounds

ELITEA-2314..2319 burned three review rounds on ONE weakness class — "presence is not data":

- round 1 raised the **Chat Messages** chart -> fixed only that chart
- round 2 raised the **Tools** chart -> fixed only that chart
- round 3 raised the **Agents bar** chart

Each round fixed the named instance and left its siblings. Every round cost a full session.

## The question to ask of every fix, before handing back

> Is there another **chart / tab / preset / KPI card / range** in this unit with the same
> weakness?

Round 3 asked it and found four more the reviewer had not reached:
- the same chart asserted on data under `Last 30d` but not under `Last 7d` (a **preset**-level
  instance — the weakness need not be a different object)
- a spec whose docstring and every step title claimed "content re-renders" while asserting only
  the request
- a subset-only chart check that a chart drawing a NARROWER older range still satisfies
- one KPI card (COST) asserted on shape while its seven siblings were asserted on value

## The structural fix that ends the class

Extract the oracle so the specs **cannot** drift apart in strength
(`automation/utils/analytics_oracles.py`). While each spec carries its own copy of an
assertion, "the other one is weaker" is a latent finding waiting for a reviewer.

## When the fix ships a GUARD, its list is the sweep surface (2026-08-29, ELITEA-2298/2299/2300)

Extraction alone is not enough. Fix round 1 did the structural fix — pulled the observer into
`utils/request_capture.collect_requests` and pinned it with a source-grep unit test — but
enumerated only the two specs the reviewer had named. The **third spec in the same unit** made
the identical "this control issued no DELETE" claim off a hand-rolled listener with no positive
control, and the guard's own module list said nothing about it. Another whole round.

So when a fix introduces a guard that enumerates its subjects:

- **The enumeration IS the sweep.** Before committing, grep the unit for the claim the guard
  polices (here: `assert not .*requests`) and reconcile the hits against the list.
- **Say so in the guard.** Its docstring now states the rule ("a delete-flow spec asserting an
  absence belongs in this list"), so the next person extending the unit has the contract.
- **Make the source grep whitespace-insensitive.** The literal-substring check would have
  missed the third spec's listener purely because it was wrapped across lines by the formatter —
  use `re.search(r'page\.on\(\s*["\']request["\']')`, and red-green it against the pre-fix
  source (`git show HEAD:<path>`), which costs one python one-liner.

Related: [[chart_presence_is_not_chart_data]] · [[recharts_interval_zero_means_exact_tick_equality]] · [[absence_of_destructive_request_needs_log_plus_positive_control]]
