---
name: MUI Select backdrop blocks a second combobox click
description: An OPEN MUI Select mounts an invisible backdrop over its own combobox — re-clicking it to "open" times out
type: feedback
aliases: [MuiBackdrop intercepts pointer events, combobox click timeout, aria-expanded select, retention measure dropdown]
tags: [area/ui, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## Symptom

`Locator.click: Timeout 10000ms exceeded` on a `*-combobox` testid, with a call log
showing `aria-expanded="true"` on the resolved element and

```
<div aria-hidden="true" class="MuiBackdrop-root MuiBackdrop-invisible MuiModal-backdrop ...">
  from <div role="presentation" id="menu-<field>" class="MuiPopover-root MuiMenu-root ...">
  subtree intercepts pointer events
```

## Cause

MUI's `Select` renders its option list in a `Popover`/`Menu` whose invisible
`MuiBackdrop` covers the whole viewport — including the combobox that opened it. So a
page-object method that unconditionally clicks the combobox to "open the dropdown"
fails whenever a caller already opened it (a very common shape: one method asserts the
offered options, the next selects one).

## Fix pattern

Make the open-click conditional, and wait for the popover to unmount before returning:

```python
if self.<x>_combobox.get_attribute("aria-expanded") != "true":
    self.<x>_combobox.click()
option = self.page.locator(self.SELECT_OPTION.format(value))
option.wait_for(state="visible", timeout=timeout)
option.click()
option.wait_for(state="hidden", timeout=timeout)   # backdrop gone before the next click
```

The trailing `hidden` wait matters as much as the conditional open: without it the
caller's next click (e.g. into an adjacent input) races the closing transition and hits
the same backdrop.

Worked example: `ArtifactsPage.select_retention_measure()` (ELITEA-1810).

Related: [[bucket_list_refetch_is_slow_on_large_projects]]
