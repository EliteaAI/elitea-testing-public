---
name: BasePage.navigate()'s real ceiling is ~70s, not the 30s networkidle leg
description: navigate() = goto(30s default) + networkidle(30s, swallowed) + spinner(10s, swallowed) + dismiss_popups — sizing a nested wait against "30s" undershoots.
type: feedback
aliases: [navigate ceiling, networkidle 30s, nested expect_response budget, CATALOG_RESPONSE_TIMEOUT, set_default_navigation_timeout]
tags: [area/page-objects, type/synchronization]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

`BasePage.navigate()` (`automation/pages/base_page.py:336-383`) has **four**
sequential waits, not one:

| Leg | Budget | Swallowed? |
|---|---|---|
| `page.goto(url, wait_until="domcontentloaded")` | 30 000 ms — `conftest.py:326` `set_default_navigation_timeout(30000)` | no (raises) |
| `wait_for_load_state("networkidle", timeout=30000)` | 30 000 ms | **yes** (`except Exception`) |
| spinner `wait_for(state="hidden", timeout=10000)` | 10 000 ms | **yes** |
| `dismiss_popups()` | unbounded-ish | n/a |

So the method's legitimate worst case is **~70 s+**, and only the middle leg is
the "30 s ceiling" people quote.

## Why it matters for a nested `expect_response`

`page.expect_response(...)` arms its waiter at the `with` **entry**, so its
budget must cover the whole wrapped body — here, all four legs — not just the
tail after the body returns.

Consequence, seen in PR #2097 (FIX #2078): `CATALOG_RESPONSE_TIMEOUT = 45_000`
is documented as clearing the ceiling "**by construction**" because 45 s > 30 s.
It does not — 45 s is still a margin that happens to hold (empirically fine:
the awaited fetch measured 9.0-10.6 s). The number is right; the stated
invariant is not. When reviewing or writing a nested-wait budget, size it
against the **sum of the enclosing call's legs**, or say plainly that it is an
empirical margin.

Related: [[network_wait_budget_must_exceed_navigate_networkidle]] (the same trap, stated before this correction) · [[wait_for_network_networkidle_races_socketio]] (#1847 — the sibling
hazard, a bare `networkidle` wait racing the persistent Socket.IO transport).
