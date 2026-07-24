---
name: MUI Switch's data-testid lands on the wrapper span, but Playwright is_disabled() still resolves correctly
description: BaseSwitch.jsx spreads data-testid onto <MuiSwitch>, which MUI renders as a data-testid-carrying MuiButtonBase-root/PrivateSwitchBase-root <span> wrapping the real <input disabled> checkbox — looked like a false-negative risk for .is_disabled(), confirmed live it is NOT.
type: feedback
---

ELITEA-2010 fix round needed to assert a pipeline node's "Interrupt before" switch
is disabled for entry-point nodes (`pipeline-node-interrupt-before-switch` testid,
wired via `EliteaUI/src/[fsd]/shared/ui/switch/BaseSwitch.jsx` spreading
`{...restProps}` — including `data-testid` — onto `<MuiSwitch>`).

**The concern:** MUI's `Switch` renders the testid-bearing element as
`<span class="MuiButtonBase-root MuiSwitch-switchBase ... Mui-disabled" data-testid="...">`
wrapping an inner `<input disabled="" type="checkbox" role="switch">`. Since a `<span>`
has no native `disabled` DOM property, the worry was that Playwright's
`Locator.is_disabled()` — which per its docs only inspects the ELEMENT ITSELF, not
descendants — would always return `False` on this locator regardless of the real
switch state, a silent false-negative.

**Confirmed empirically (temporary debug print, outerHTML + is_disabled() dump against
a live entry-point node), not assumed:** `.is_disabled()` on the testid'd `<span>`
correctly returned `True` when the underlying `<input>` had `disabled=""`. So Playwright's
disabled check for this MUI Switch shape is reliable straight off the class-level
`LocatorDescriptor(testid=...)` — no need to chain `.locator("input")` off it (which
would ALSO violate the page-object rule against raw selectors chained off an existing
field anyway).

**Takeaway:** don't assume a testid sitting on a MUI wrapper element (span/div around
the real form control) makes `is_disabled()`/`is_checked()`/similar state assertions
unreliable — verify with a one-off debug print (outerHTML + the assertion's return
value) against the live app before deciding a raw-selector workaround or a stop+flag
escalation is needed. This BaseSwitch/MuiSwitch shape is reused across many other
switches in this codebase (Structured output, Interrupt after, memory/settings
toggles) — the same reasoning applies to all of them.
