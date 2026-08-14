---
name: A generic expect_response/capture_requests_matching predicate can resolve on the WRONG parallel request
description: When several requests share a URL substring (bulk + Trending + My-Liked on Catalog mount/clear), a same-substring predicate can match the fast one, not the one that drives the DOM you're about to read — scope the predicate.
type: feedback
---

## What happened (ELITEA-2363, AgentHubPage.clear_search)

Clearing the Catalog search field re-fires the SAME 3-request pattern as
initial page mount: a bulk all-applications call
(`?query=&...limit=1000`), a Trending call (`trend_start_period=...`), and
a My-Liked call (`my_liked=true`) — all three share the
`/public_applications/prompt_lib/` URL substring.

The first version of `clear_search()` used:

```python
with self.page.expect_response(
    lambda r: "/public_applications/prompt_lib/" in r.url and r.request.method == "GET",
    timeout=timeout,
):
    ...press Backspace...
```

This context manager returns as soon as **any** matching response arrives
— which in practice was often the faster, smaller Trending/My-Liked call
(`limit=20`), not the bulk call that actually repopulates the main content
grid. `wait_for_network()` (networkidle) afterwards did NOT reliably save
this — by the time all 3 requests settle, `networkidle` fires, but reading
the DOM immediately after can still race a render that hasn't flushed.

Symptom: reading the card list right after `clear_search()` returned still
showed the pre-clear FILTERED set (6 cards), not the restored baseline (23
cards) — looked like "clear didn't work" but the field's `input_value()`
was correctly empty; only the content grid was stale.

## The fix

1. Scope the `expect_response` predicate to the SPECIFIC request that
   drives the thing you're about to assert on — the same distinguishing
   filter `AgentHubPage.navigate_and_capture_applications()` already used
   (exclude `trend_start_period` and `my_liked` to isolate the bulk call).
2. Add a retrying assertion for the post-response DOM state instead of
   trusting network-settle timing alone —
   `expect(locator).to_have_count(expected)` /
   `.not_to_have_count(previous)` — mirroring the existing
   `wait_for_like_count()` idiom on this same page object.

## Generalize

Any time you write/reuse `expect_response(...)` or
`capture_requests_matching(url_substring, ...)` and the substring can match
**more than one concurrently-firing request**, don't assume "the response I
wanted" == "the first response that matched". Check whether other requests
share the substring (grep the page's mount-time network calls, or read the
AFS's § Network Behavior section) and add a distinguishing filter if so.
This bit `clear_search()` here; it can bite any Catalog/dashboard action
that re-triggers a multi-request mount pattern (bulk + Trending + My-Liked
is specifically an Agent Hub / Skills Hub thing — check for the analogous
pattern before reusing this idiom elsewhere).
