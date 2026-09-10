---
name: An allure step with the SAME duration on pass and fail is a fixed budget, not a wait
description: Three params at 3060/3071/3074 ms settled a [FIX] root cause in one script — a real wait varies with the backend, a sleep does not
type: feedback
aliases: [step duration identical, fixed sleep budget, networkidle returns instantly, false red on a successful save, wait_for_timeout, premature assertion, socket.io networkidle]
tags: [area/triage, type/lesson]
created: 2026-09-10
updated: 2026-09-10
---

## The tell

Dump every allure step's duration for ALL params of a failing parameterized test,
passing ones included. **A step whose duration is near-identical across params and
across outcomes is a fixed budget, not a wait on the system.**

Worked case #2123 / ELITEA-1141: Step 7 ("Click Save") = **3060 / 3071 / 3074 ms**
in all three params, pass and fail alike; the failing Step 8 then took **0-3 ms**.
A real wait on a backend POST cannot be that stable. The code was:

```python
page.wait_for_load_state("networkidle", timeout=FORM_SAVE_TIMEOUT)
page.wait_for_timeout(3000)          # <- this was the ENTIRE budget
assert "/toolkits/create" not in page.url    # read instantly, no wait
```

## Why `networkidle` contributes nothing here

This app holds a **persistent `/socket.io/` poll**, so `networkidle` (500 ms of zero
connections) resolves in ~0.05 s — the #1847 mechanism. Any
`wait_for_load_state("networkidle")` + `wait_for_timeout(N)` pair in this suite is
**really just `sleep(N)`**. There are ~140 `wait_for_network` call sites; treat the
pair as a false-RED generator wherever a backend round-trip follows it.

## The verdict it produces

**A false RED on a SUCCESSFUL operation** — the object was created, the assertion
just fired too early. Two consequences that are easy to miss:

1. The CI message names the wrong subsystem ("did not navigate away"), so triage
   goes hunting a product regression that does not exist.
2. **Passing runs can leak too.** If teardown keys off a lookup that never ran, every
   slow run leaks a real object into the CI project.

## The repair shape

Wait on the **real request** (`expect_request`/`expect_response` on the create POST),
assert its status and body, and take the object id from the RESPONSE — never from a
later name lookup. Then prove it three ways: pre-repair fails, repaired passes with
the real response delayed, and repaired **fails at the new step** when the request is
blocked entirely. The third control is the one that proves you did not buy green by
going blind.

Related: [[env_outage_page_is_a_fix_card_root_cause]] · [[name_a_precedent_as_a_hypothesis_not_a_conclusion]]
