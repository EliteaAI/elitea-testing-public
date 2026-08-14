---
name: /settings/memory autosave — wait for the GET refetch too, not just the PUT
description: Two rapid toggle clicks on /settings/memory (Context Management) can race — the first click's GET .../author/ refetch resolving AFTER a second click reverts DOM state. wait_for_autosave()'s networkidle wait never settles here (persistent WebSocket) so its 1s fallback isn't enough — wait for both PUT and GET via page.expect_response() before reading state.
type: feedback
---

## The situation

ELITEA-2374 (Context Management toggle). `UserProfileSettingsPage`'s
`enable_context_management()` / `disable_context_management()` click the
toggle then call `wait_for_autosave()`, which tries `wait_for_network()`
(networkidle, 5000ms) then falls back to a 1s `wait_for_timeout`. On
`/settings/memory` networkidle NEVER settles (persistent WebSocket keeps
the connection alive — this is documented in the page object's own
docstrings), so every call silently takes the 1s fallback path.

Confirmed live: each toggle click fires `PUT /api/v2/social/author/` → 200
immediately, followed by a `GET /api/v2/social/author/` refetch a short
time later. If a SECOND toggle click fires before the FIRST click's GET
refetch resolves, the late-arriving GET response can overwrite the second
click's local state change when it lands — read
`is_context_management_enabled()` right after the second click and it can
still show the PRE-second-click value, even though the second click's own
PUT already returned 200. Not reliably reproducible on every run (empirically
seen once in ~4 attempts) — genuinely timing-dependent, not deterministic.

## Why it matters

A test that does precondition-enable (step 2) then disable (step 5) close
together — the realistic AFS-driven shape for a toggle test — can hit this.
The 1s `wait_for_autosave()` fallback is not a reliable synchronization
point on this page; don't trust it before firing a second state-changing
action.

## Fix pattern

Wait for BOTH responses (PUT and its GET refetch) via nested
`page.expect_response()` context managers, registered before triggering the
action:

```python
def _is_autosave_put_response(response): 
    return response.request.method == "PUT" and "/api/v2/social/author/" in response.url

def _is_autosave_get_response(response):
    return response.request.method == "GET" and "/api/v2/social/author/" in response.url

with page.expect_response(_is_autosave_get_response, timeout=10000) as get_info, \
     page.expect_response(_is_autosave_put_response, timeout=10000) as put_info:
    profile.disable_context_management()
assert put_info.value.status == 200          # what the AFS actually asserts
_ = get_info.value                            # consumed only to settle the race
assert not profile.is_context_management_enabled()
```

Nesting order doesn't matter — both listeners attach before the action runs
(Python's `with A, B:` enters A then B), so it's safe regardless of which
response actually arrives first.

## Reusable check

Before writing ANY test that fires two state-changing autosave actions in
sequence on this page (or any page with a persistent-WebSocket-blocked
`wait_for_network()`), don't trust `wait_for_autosave()`'s fallback timing —
wait on the concrete PUT+GET pair explicitly around each action instead.
