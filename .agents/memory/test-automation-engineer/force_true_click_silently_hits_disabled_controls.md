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
dev.elitea.ai it was measured at 0.002 s–0.411 s and is unbounded under load.
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

Worked fix: `PipelineDetailPage.open_trigger_select()` (`TRIGGER_SELECT_ENABLED`
/ `TRIGGER_SELECT_EXPANDED`). Measured on dev.elitea.ai 2026-08-28: clicking
while `aria-disabled="true"` was swallowed 3/3; waiting for enabled first opened
the menu in 1-2 ms, 5/5, and cut ~3 s of wasted probe off every open.
