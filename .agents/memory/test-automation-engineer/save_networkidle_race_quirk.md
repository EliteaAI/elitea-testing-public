---
name: Save-click networkidle race when asserting captured network responses
description: click_save()'s wait_for_network() (networkidle) can resolve before the app's debounced Save PUT is even dispatched, so a captured-request status check right after click_save() returns can race the fetch — poll instead of trusting networkidle
type: feedback
---

## The quirk

`AgentFormPage.click_save()` (and its siblings `save_and_wait()` /
`save_and_wait_for_navigation()`) do:

```python
self.save_button.evaluate("el => el.click()")
self.wait_for_network(timeout=timeout)  # page.wait_for_load_state("networkidle")
```

`wait_for_load_state("networkidle")` is satisfied when there are **zero
in-flight network connections for 500ms**. If the app's Save handler debounces
before actually dispatching the PUT (a small `setTimeout`/microtask delay
between the click and the fetch), `networkidle` can be trivially true
*immediately* after the click — there's nothing in flight yet — and
`wait_for_network()` returns almost instantly, **before the Save request has
even started**.

This is invisible if you only assert on UI end-state (e.g. "Save button goes
back to disabled", "the value round-trips after reload") because those
end-states become true eventually regardless of when you checked. It bites
the moment a test asserts on a **captured network response** right after
`click_save()` returns — e.g. via `BasePage.capture_requests_matching()`
(`agent_detail_page.py`'s pattern, used for e.g. attach/detach PATCH
assertions) applied to the Save PUT specifically.

Confirmed live (ELITEA-1884 implementer pass) via raw `page.on("request"/
"response"/"requestfinished")` event tracing: the PUT to
`.../application/prompt_lib/{project}/{agent_id}` showed up as a captured
**request** in the list, but its **response** event hadn't fired by the time
the very next line's assertion ran — `wait_for_network()` had already
returned. Adding a bare `page.wait_for_timeout(3000)` after `click_save()`
made the response show up (status 201), confirming it was a pure timing race,
not a real product delay or defect.

## The fix (test-local, not a page-object change)

`click_save()` itself is a shared-caller method (many other tests rely on its
exact current behavior/timing) — don't touch it for a single test's assertion
need. Instead, poll the captured-request list for a resolved status instead
of trusting `networkidle`:

```python
def _wait_for_resolved_save_count(page, save_requests, expected_count, timeout=15000):
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        resolved = [r for r in save_requests if r["status"] is not None]
        if len(resolved) >= expected_count:
            return
        page.wait_for_timeout(200)
```

Call it right after `detail_page.click_save(...)`, with `expected_count`
incrementing per Save click in the test (1 after the first Save, 2 after the
second, etc.) — mirrors the polling pattern already used elsewhere in
`agent_detail_page.py` for RTK-Query-cache-driven state (`attach_skill()`'s
skills-counter poll, `wait_for_skills_counter()`).

**Timeout budget note**: 8000ms was NOT always enough — one local run needed
closer to the full 15000ms window before the second Save's PUT resolved
(likely a slower Vite dev-server / HMR moment, not a systemic slowness). Use
15000ms as the default budget for this specific poll, not the project's usual
8-10s UI-element timeout.

## Generalization

Any future test asserting on a Save/Attach/Detach network response captured
via `capture_requests_matching()` **immediately** after the triggering click
should poll the captured list for a resolved status rather than assuming
`wait_for_network()` / `networkidle` guarantees the request has even started.
The existing `add_mcp()`/`add_toolkit()` methods dodge this by inserting an
explicit `page.wait_for_timeout(1000)` *before* their own `wait_for_network()`
call — that pre-delay is why those don't exhibit the race, not because
`networkidle` is inherently reliable for debounced actions.

(from ELITEA-1884 implementer pass, PR #536)
