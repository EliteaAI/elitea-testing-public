---
name: Absence guards must watch the real mechanism, not a nearby proxy
description: A "X did not happen" assertion is only real if it watches the signal X actually produces — read the handler before picking the signal
type: feedback
aliases: [negative assertion, did-not-happen guard, fail criterion, no action assertion, popup guard]
tags: [area/ui-tests, type/assertion-quality]
created: 2026-08-24
updated: 2026-08-24
---

## The failure shape

A case's Fail criterion is often negative — "Cancel triggers an authorization
attempt", "the row is not deleted", "no request is sent". It is very easy to
write a guard that *looks* rigorous (a request counter, a network listener) and
is in fact **vacuous**, because the action being guarded against produces a
completely different signal. Such a guard is green forever and can never fail —
worse than no guard, because it reads as coverage.

Caught in review on ELITEA-1982 (2026-08-24): step 9 guarded "Cancel must not
authorize" by counting `POST /configurations/check_connection/` requests. But
`McpAuthModal.onAuthorize` (`McpAuthModal.jsx:244-258`) opens
`window.open('about:blank','_blank')` and runs the whole OAuth handshake **inside
that popup** — it issues no `check_connection` and nothing the parent page's
`page.on("request")` can observe. Clicking Authorize would have left the old
guard perfectly green.

## The rule

Before writing any absence assertion, **open the handler for the action you are
asserting did NOT happen** and name its first unconditional observable effect.
Guard THAT. Then check the guard is not vacuous by making the action happen once
(red) and reverting (green) — a negative assertion that has never been seen to
fail is unverified.

Watch for guards that are invisible-by-construction:
- work that happens in a **popup / new tab** — the parent page's request and
  console listeners see none of it. Use `page.on("popup")` plus a
  `len(page.context.pages)` delta (the latter is a synchronous re-read, immune
  to event-timing races).
- work in an **iframe**, a **service worker**, or a `sendBeacon` / `fetch(keepalive)`.
- work that only writes **localStorage / IndexedDB**.

Also: leave teardown that closes anything the guard's failure would leak (a
popup left open outlives the test and pollutes the next one).

Related: [[credential_form_blur_commits_value]]
