---
name: force=True click silently hits disabled controls
description: force=True skips Playwright's enabled check, so a click on a loading/disabled MUI control is dispatched, does nothing, and hangs the next wait
type: feedback
---

`locator.click(force=True)` skips **all** actionability checks — including
**enabled**. The click is still dispatched at the coordinates, MUI's handler
sees `disabled` and returns, and nothing happens: **no exception, no log, no
effect**. The symptom always surfaces one step later, as a long timeout on
whatever the click was supposed to produce — which sends you hunting in the
wrong place (overlay interception, remount, stale locator).

**This repo is full of `force=True`** (canvas overlay interception makes it
necessary), so the trap is everywhere, not just on one surface.

**Why it bites on remote envs specifically:** many Elitea controls are disabled
while an RTK-Query GET is in flight, e.g.
`TriggerTypeSelector.jsx`: `disabled={disabled || isLoading}` with `isLoading`
from `useGetPipelineTriggerQuery`. On localhost that window is ~3 ms; on
dev.elitea.ai it was measured at 0.002 s–1.076 s over a 15-reload sample, and as
high as **19.99 s** on a degraded environment — far past any interaction-sized
timeout, directly observed, not inferred.
A fixed-duration retry ("wait 3 s, click again") is therefore a coin flip, and
when it loses it wastes its one retry and hangs the full timeout — issue #1895,
ELITEA-2008 Step 8.

**The rule: gate the click on STATE, never on elapsed time.** MUI puts both
states on the control's own node, so no new testid is needed:

* `aria-disabled="true"` — present when disabled, **ABSENT** (not `"false"`)
  when enabled ⇒ filter with `:not([aria-disabled="true"])`.
* `aria-expanded="true"|"false"` — for Select/menu triggers.

For MUI `Select`, the readable node is the SelectDisplay; this repo's
`SingleSelect.jsx` gives it `data-testid="<select testid>-combobox"`
(`SelectDisplayProps`), already on EliteaUI `main`. Attribute source:
`node_modules/@mui/material/Select/SelectInput.js:474-475`.

Also: **never re-click a control whose menu may already be open.** MUI's Menu
mounts a full-viewport Modal backdrop, so a forced coordinate click lands on the
backdrop and toggles the menu shut. Re-read `aria-expanded` immediately before
every click; an option `count()` sampled earlier does not prove "still closed".

**And give that wait its OWN budget — it is a network wait wearing an
interaction wait's clothes.** Callers pass `UI_ELEMENT_TIMEOUT` (10 s, sized for
a local DOM click), but what gates "is this control enabled yet" is a remote
round-trip. Sharing one budget lets a slow GET eat the whole allowance the
click/retry loop needs afterwards, and the test then fails on the *interaction*
having no time left rather than on anything it verifies. Split them: a
network-sized constant for the wait-for-ready leg, the caller's tighter timeout
for the click/expand loop. This is not a blanket timeout increase — only the
precondition leg gets the bigger number, and the failure must still fire loudly
when it genuinely expires.

**Make the failure name the state.** `select present=N, enabled=N, expanded=N,
options=N` distinguishes "never rendered" / "never enabled" / "opened but empty"
— three different causes that an opaque `wait_for` reports identically. That
message is what let the next reader classify the residual in one glance instead
of re-deriving it.

Worked fix: `PipelineDetailPage.open_trigger_select()` (`TRIGGER_SELECT_ENABLED`
/ `TRIGGER_SELECT_EXPANDED` / `TRIGGER_SELECT_READY_TIMEOUT`). Measured on
dev.elitea.ai 2026-08-28: clicking while `aria-disabled="true"` was swallowed
3/3; waiting for enabled first opened the menu in 1-2 ms, 5/5, and cut ~3 s of
wasted probe off every open. Causality captured live — in a 15-reload sample the
disabled window ended **46 ms after the `pipeline_trigger` GET finished**
(window 1.076 s, GET finished at 1.03 s), so the state provably tracks the
round-trip.
