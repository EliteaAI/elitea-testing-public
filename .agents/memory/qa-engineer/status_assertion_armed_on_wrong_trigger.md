---
name: Status assertion armed on the wrong trigger is a vacuous green
description: Verify WHICH user action actually issues a request before asserting its status — a listener armed on the wrong action asserts nothing and always passes
type: feedback
aliases: [vacuous assertion, expect_response, response listener, http status assertion, false green]
tags: [area/test-design, type/false-green]
created: 2026-08-22
updated: 2026-08-22
---

## The failure mode

A TMS case says *"open X — verify `GET /y/` returns 200 (not 500)"*. The obvious automation is to arm a
response listener around the click that opens X. If the request is actually issued **somewhere else**
— a mount effect, a parent route load, a prefetch — then:

- the listener collects **nothing**,
- `all(r.status == 200 for r in collected)` over an **empty list is `True`**,
- the test is green, forever, on every environment, including one where the endpoint returns 500.

It survives review (there IS an assertion, it IS strong, it DOES match the AFS) and it survives an
N×-green merge gate perfectly, because it never touches the network at all.

## The check that costs 30 seconds

Before writing the assertion, capture the network **across the candidate trigger in isolation** and look
at the list. Empty ⇒ you are arming the wrong action. Then read the component: a request in a mount
`useEffect` belongs to the page load, not to the button that renders its cached result.

Guards worth keeping in the delivered spec:

```python
assert collected, "no GET /… observed — listener armed on the wrong trigger"
assert all(r.status == 200 for r in collected), [r.status for r in collected]
```

The non-empty assertion is the load-bearing half. Also assert **every** occurrence, not the first:
React StrictMode double-invokes mount effects in dev, so list endpoints commonly fire twice, and
`expect_response` returns only the first — a second-call 500 would slip through.

## Worked instance

ELITEA-2423 (Support Assistant history after refresh), 2026-08-22.
`GET /api/v2/support_assistant/conversations/` fires in `initAssistant.hook.ts:44` (mount effect), so it
is triggered by the **page reload**, while the case text attributes it to opening the History panel.
Measured live: **zero** requests during the History click; `[200, 200]` across the reload. Recorded in
`test-specs/support-assistant/_surface.md` quirk 26 and clarification issue #1649.

Related: [[project_briefing]]
