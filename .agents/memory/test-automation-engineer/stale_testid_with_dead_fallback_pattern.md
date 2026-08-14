---
name: Stale testid + dead fallback = silently-broken locator
description: LocatorDescriptor.__get__ resolves testid first and never falls through to `fallback` once a testid is set — a stale/renamed testid on a legacy field (one still carrying the old `fallback=` param) doesn't degrade gracefully, it just times out. Confirmed twice (ELITEA-1870 create_agent_button, and the sibling AgentFormPage.cancel_button gap flagged in the same case).
type: feedback
---

`pages/locator_descriptor.py`'s `__get__` resolves in strict priority order:
`testid` > `locator` > `fallback`. If `testid` is set (even to a value that no
longer exists in the live DOM), the method returns `page.get_by_test_id(...)`
immediately — `fallback_fn` is **dead code**, never invoked, regardless of
whether the testid actually resolves to anything live.

This means a legacy `LocatorDescriptor(testid="old-name", fallback=lambda
page: ...)` that predates a UI rename doesn't "gracefully fall back" the way
the parameter name implies — it just breaks, and breaks silently until
something actually exercises that field (a `.click()`, `.is_visible()`,
`.input_value()` etc. that times out).

**Real case (ELITEA-1870):** `AgentsListPage.create_agent_button` carried
`testid="create-agent-button"` (0 live matches, confirmed via a full
`document.querySelectorAll('[data-testid]')` inventory on `/agents/all`) plus
a `fallback=lambda page: page.get_by_label("Create Agent").get_by_role(...)`
that also didn't match live. Nothing had ever called `click_create_agent()`
before this case (confirmed via repo-wide grep) so the break was never
surfaced. Fixed by pointing the testid at the real live value
(`sidebar-create-button`) and dropping the fallback param entirely, per the
testid-only locator policy.

**Same AFS flagged a second instance, left unfixed (out of scope for that
case):** `AgentFormPage.cancel_button` carries `testid="agent-cancel-button"`,
also not present live (confirmed: `document.querySelector` → null), with a
role-based fallback that DOES resolve live (`get_by_role("button",
name="Cancel")` — the button renders correctly, just without its testid).
Do NOT assert on `cancel_button` state in new tests until its testid is
fixed via `add-data-testid` — it will time out, not fall back.

**Actionable pattern for future implementer passes:** when an AFS's Concrete
Handles table flags a testid as "not found live" on a field that still has a
`fallback=` param, don't assume the fallback protects you — check whether
anything actually calls that field/method yet. If nothing does, it's a
silent break waiting to be discovered exactly like ELITEA-1870's was. If the
AFS marks the fix out-of-scope for the current case, skip asserting on that
field rather than trusting the fallback to cover you.
