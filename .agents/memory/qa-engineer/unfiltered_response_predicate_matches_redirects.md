---
name: An unfiltered expect_response predicate matches REDIRECTS, not just the final response
description: Dropping `status == 200` from a response predicate makes 3xx hops win the wait — eliteaApi follows redirects and retries after auth popups
type: feedback
aliases: [expect_response status filter, redirect wins the wait, response predicate 3xx, status==200 predicate]
tags: [area/playwright, type/anti-pattern]
created: 2026-09-10
updated: 2026-09-10
---

## The trade nobody states out loud

A predicate filtered on `response.status == 200` makes a FAILED fetch never match, so the
wait burns its whole budget and reports a blind timeout (real problem — FIX #2169,
ELITEA-2367). The reflex fix is to drop the status filter and judge the response after the
wait. That reflex has a cost the fix rounds keep missing:

**`page.on("response")` / `expect_response` fire for REDIRECT responses too.** A 30x on the
awaited URL carries the *requested* URL, so it matches any url-fragment predicate, and
`response.ok` is False for it. The wait therefore resolves on the redirect hop and the code
raises "backend fault" for a request the app went on to complete successfully.

In THIS app that is not hypothetical: `EliteaUI/src/api/eliteaApi.js`'s `fetchBaseQuery`
`fetchFn` follows redirects (`response.redirected`), and on a forward-auth session-expiry
redirect it opens an auth popup and **re-fetches the original request**. Pre-drop, the 302
was skipped and the retried 200 satisfied the wait. Post-drop, the 302 hard-fails the run
with a message asserting a backend fault — reintroducing the subsystem-misnaming the card
existed to remove.

## What to do instead

- Keep the predicate status-agnostic **except** for redirects: exclude `300 <= status < 400`.
- The diagnosability win does NOT depend on dropping the filter: the #2078
  `_expect_endpoint_response` listener records EVERY status on the family, so a 404 that
  never matches still prints as `observed: ['404 <url>']` in the re-raised timeout. Dropping
  the filter buys **speed** (45 s -> ~7 s), not naming.
- A "forced 404" measurement proves the fast path, never the traffic shape around a REAL
  failure. Read the app's fetch layer before trusting an unfiltered predicate.

Related: [[status_filtered_response_predicate_hides_the_failure]]

## Settled: exclude 3xx on the PREDICATE, never `redirected_from`

Round-1 outcome on PR #2203 (FIX #2169), recorded so nobody re-opens it:

- `and not (300 <= response.status < 400)` on the predicate is the whole fix. The
  recorder keeps NO status filter, so the hop still prints under "responses observed
  meanwhile" — the diagnostic is lossless, and a unit pin asserts exactly that.
- **Do not also exclude `response.request.redirected_from`.** A terminal response that
  carries `redirected_from` and sits on the awaited URL is the *legitimate answer* in
  every real shape: an http->https or 307/308 same-path upgrade, or a forward-auth
  bounce that lands back on the original URL. Excluding it would skip the real response
  and re-create the 45 s blind timeout the card removed.
- A `route.fulfill(302, location=<same url>)` probe produces a self-redirect whose
  terminal response has an unreadable body. That is an artifact of the probe, not a
  backend shape — the real re-auth 302 points at `/forward-auth/.../login`, which cannot
  match an endpoint-fragment predicate at all.
