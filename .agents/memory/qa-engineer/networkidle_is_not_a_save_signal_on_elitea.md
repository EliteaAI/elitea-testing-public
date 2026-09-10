---
name: networkidle is not a save signal on Elitea — measured 0.05 s
description: wait_for_load_state("networkidle") + wait_for_timeout(N) is a hard N-second budget for a backend call
type: feedback
aliases: [networkidle, wait_for_load_state, fixed sleep after save, save race, premature assertion]
tags: [area/waits, type/anti-pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The measurement

On `localhost:5173`, `page.wait_for_load_state("networkidle", timeout=15000)` immediately
after a Save click returned in **0.05 s** — while the real create POST was still in
flight. Corroborated by CI allure timings: the enclosing step took **3 060 / 3 071 /
3 074 ms** across three params, i.e. the `wait_for_timeout(3000)` and nothing else.

Mechanism: the app holds a persistent `/socket.io/?EIO=4&transport=polling` connection,
so "500 ms of network silence" either never arrives or arrives arbitrarily
(`.agents/testing.md` #1847). Either way it carries **zero information about the request
you care about**.

## The consequence

`wait_for_load_state("networkidle") + wait_for_timeout(N)` is not a wait — it is a
**hard N-second budget** for an asynchronous backend call, followed (usually) by an
instantaneous assertion. On a loaded environment the budget expires and the test reports
the wrong subsystem: *"the form did not navigate"* for a save that succeeded.

## The replacement

Wait on the thing itself:

```python
with page.expect_response(lambda r: "/elitea_core/tools/prompt_lib/" in r.url
                                     and r.request.method == "POST", timeout=30_000) as resp:
    save_button.click()
assert resp.value.status == 201
created_id = resp.value.json()["id"]        # capture BEFORE anything else can raise
page.wait_for_url(re.compile(rf"/toolkits/all/{created_id}(\?.*)?$"))
```

Same family as #1847's prescribed fix: wait on what the caller actually needs, never on
network silence. Origin: #2123 / ELITEA-1141, 2026-09-10.

Related: [[both_save_and_cancel_greyed_means_isloading]]
