---
name: A positive-existence retry wait cannot safely assert a negative transition
description: A helper shaped `locator(X).wait_for(state="visible")` only retries until X APPEARS. Negating its bool result to assert "no longer X" right after a click races the optimistic DOM update — write a dedicated auto-retrying wait for the negative case (expect().to_have_attribute(...)).
type: feedback
---

## What happened (ELITEA-2355, Agent Hub unlike-from-list-view)

`AgentHubPage.is_agent_liked(application_id)` (ELITEA-2354) is implemented as:

```python
liked_locator = self.page.locator(LIKE_BUTTON.format(id) + '[data-liked="true"]')
try:
    liked_locator.wait_for(state="visible", timeout=timeout)
    return True
except Exception:
    return False
```

This is a **retry-until-APPEARS** check — correct for "wait until this
becomes liked" (used by every prior like case). ELITEA-2355 (unlike) needed
the opposite: "wait until this is no longer liked, right after clicking
unlike." The natural-looking `assert not agent_hub.is_agent_liked(id)`
failed on the FIRST run with a clean click + 204 response already confirmed
— because the CSS selector `[data-liked="true"]` still matched the stale
DOM at the instant of the check (the like/unlike attribute flip is
optimistic-client-side and lands a beat after the network response
resolves, same class of race as this page's own `get_like_count` docstring
already documents for the count). `.wait_for(state="visible")` found the
stale "true" match INSTANTLY and returned — it never got the chance to
retry, because retrying-until-APPEARS has nothing to retry when the thing
is already (stale-)present.

## The fix

Added `AgentHubPage.wait_for_liked_state(application_id, liked: bool, ...)`
using Playwright's native auto-retrying assertion:

```python
expect(button).to_have_attribute("data-liked", "true" if liked else "false", timeout=timeout)
```

This retries on the ATTRIBUTE VALUE itself (either direction), not on
element-presence, so it correctly waits out the race whichever way the
state is transitioning. Use this for any transition-right-after-a-click
assertion; keep the boolean-returning presence check for baseline /
already-settled reads only.

## Generalize

Any project helper shaped "poll for the element/state to APPEAR, return
bool" is a **one-directional** wait. Negating its result to assert the
opposite direction is only safe when you're confident nothing async is
in flight (e.g. reading a value that hasn't been touched this test). The
moment you're asserting "X flipped to NOT-Y right after I clicked
something", reach for (or add) a wait keyed on the ATTRIBUTE/TEXT VALUE
itself (`expect(locator).to_have_attribute(...)` /
`expect(locator).not_to_have_attribute(...)` / `to_have_text(...)`), never
`not <presence-check>()`.
