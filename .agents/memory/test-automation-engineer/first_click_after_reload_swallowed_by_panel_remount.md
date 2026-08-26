---
name: First click after a page reload is swallowed by a config-panel remount
description: Post-reload, selecting a ReactFlow node remounts its config panel and replaces the just-resolved control — the click lands on a dead element and the wait burns its full timeout.
type: feedback
aliases: [swallowed click, dropdown never opens, post-reload click, open_trigger_select retry]
tags: [area/flakiness, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## Symptom

After `page.goto(url)` + canvas load, the first `click(force=True)` on a control inside a
ReactFlow node's config panel does nothing: the menu never opens, and the follow-up
`wait_for(state="visible")` expires against its FULL timeout. An immediate second click opens
it. Reproduced 3/3 at 10 s on the pipeline entry-point Trigger select (ELITEA-2008, 2026-08-26).

## Why it is NOT slowness

A 10 s wait that sees nothing, followed by an instant success on re-click, rules out "the app
was slow". Selecting the node remounts its config panel, so the element resolved a moment
earlier is replaced before the click lands — `force=True` happily clicks a dead element.
**Raising the timeout is the wrong fix and buys nothing.** Re-clicking re-resolves the locator.

## The shape of the fix

```python
try:
    options.first.wait_for(state="visible", timeout=SHORT_PROBE)   # 3s
except PlaywrightTimeoutError:
    if options.count() == 0:      # the click never landed at all
        control.click(timeout=timeout, force=True)
    options.first.wait_for(state="visible", timeout=timeout)
```

The `count() == 0` guard is load-bearing: without it, a menu that is merely rendering slowly
gets clicked SHUT by the retry, converting a slow pass into a hard fail. Guard the retry on
"no evidence the action took effect at all", never on "not finished yet".

This also keeps the change backward-compatible for every existing caller of a shared opener —
it can only turn a would-be timeout into a success, so it is safe to put in the shared method
rather than duplicating a private one.
