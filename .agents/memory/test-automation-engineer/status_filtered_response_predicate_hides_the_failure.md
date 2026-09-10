---
name: A status-filtered expect_response predicate turns a failed fetch into a blind timeout
description: Don't filter an expect_response predicate on `status == 200` — but DO exclude 3xx, or redirect hops win the wait.
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

## The correction that makes it safe — exclude 3xx (learned the same day, in review)

"Match anything, judge after" is **half a rule**. `page.on("response")` and
`expect_response` also fire for **redirect hops**, and a 30x carries the *requested*
URL — so an unfiltered predicate happily takes the hop, sees `ok == False`, and reports
a backend fault. Verified live on DEV (302 forced on the endpoint): the hop won the wait
and raised `HTTP 302 Found … backend/app fault` — the wrong-subsystem harm the change was
made to remove, reintroduced by the fix for it.

It is not theoretical on this app: `EliteaUI/src/api/eliteaApi.js`'s
`fetchBaseQuery.fetchFn` handles `if (response.redirected)` and, on a forward-auth
session-expiry redirect, opens an auth popup and **re-fetches the original request**. The
retried 200 is the answer; the 302 is transport. A status-filtered predicate survived
re-auth by accident; an unfiltered one breaks on it.

⚠️ Also seen in that probe: a redirect-chain terminal response (`request.redirected_from`
set) can match on the same URL with an **unreadable body** — so any `response.text()` in a
diagnostic path needs its own try/except, or the handler whose job is naming things dies
with a raw traceback instead.

## The shape

**Match on identity (URL + method), EXCLUDE redirect hops, judge status and body after.**

```python
def _is_terminal(response):
    return FRAGMENT in response.url and response.request.method == "GET" and not (300 <= response.status < 400)

with self._expect_endpoint_response(_is_terminal, timeout, "agent-categories", url_fragment=FRAGMENT) as info:
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
