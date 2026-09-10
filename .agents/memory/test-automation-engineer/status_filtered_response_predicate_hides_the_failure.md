---
name: A status-filtered expect_response predicate turns a failed fetch into a blind timeout
description: Never put `status == 200` in an expect_response predicate — match the request, then judge the response.
type: feedback
aliases: [expect_response predicate, status 200 predicate, blind timeout, categories await, agent_categories oracle]
tags: [area/playwright, type/anti-pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The anti-pattern

```python
def _is_categories_response(response):
    return FRAGMENT in response.url and response.request.method == "GET" and response.status == 200
```

It reads like defensive care. It is the opposite: a **failed** fetch never matches, so the
wait cannot resolve, burns its whole budget (45 s here), and then reports
`Timeout 45000ms exceeded while waiting for event "response"` — about a request that
already came back, with its status nowhere in the message. The one failure mode you most
need named is the exact one the filter erases.

Measured on `dev.elitea.ai` (ELITEA-2367 / FIX #2169), categories fetch forced to 404:

| | Wall clock | Message |
|---|---|---|
| status-filtered predicate | **45.05 s** | `Timeout 45000ms exceeded while waiting for event "response"` |
| unfiltered + explicit judgement | **7.37 s** | `HTTP 404 Not Found for https://…/agent_categories/prompt_lib/1` |

## The shape

**Match on identity (URL + method); judge status and body after the wait.**

```python
with self._expect_endpoint_response(pred, timeout, "agent-categories", url_fragment=FRAGMENT) as info:
    super().navigate("/elitea-catalog")
response = info.value
if not response.ok:
    raise AssertionError(f"... returned HTTP {response.status} {response.status_text} for {response.url} ...")
```

Two companions, both learned the same day:

- **Judge BEFORE the UI-readiness wait**, so a backend fault surfaces in ~its own round trip.
- **Never `.get(key, [])` a captured oracle payload.** Degrading a failed or contract-broken
  response into "empty" converts a backend fault into a *content delta* in the caller's
  assertion — a loud red naming the wrong subsystem. Name the missing key instead.

## When the wait genuinely can't resolve

Wrap it so the timeout names **its own** endpoint family's observed traffic (`['none']` = it
never fired, vs a list = siblings landed and this one alone was slow). A diagnostic recorder
keyed on a family the caller is not waiting on prints `['none']` every time and actively
misleads — so pass the family in, never hardcode it in a shared helper.

Related: [[dev_page_goto_flake_is_a_precondition]] · [[a_settle_can_be_fragile_and_vacuous_at_once]]
