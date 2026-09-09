---
name: Diagnostic readback in an error handler needs its own short timeout
description: An unguarded get_attribute/text_content inside a give-up path can time out and mask the informative failure it was written to describe.
type: feedback
aliases: [diagnostic readback, DIAGNOSTIC_READBACK_TIMEOUT, give-up path masks failure, get_attribute in except]
tags: [area/page-objects, type/review-check]
created: 2026-09-09
updated: 2026-09-09
---

## The pattern

A page-object method that gives up after N attempts often reads live state back
to build an informative error:

```python
trigger_state = self.page.locator(self.X).get_attribute("aria-expanded")
raise AssertionError(f"... still reports aria-expanded={trigger_state!r} ...")
```

If the element is **detached** by then (navigation, unmount, a full-page error
page), `get_attribute` waits the context default (`conftest.py:325` sets
10 000 ms) and raises `PlaywrightTimeoutError: Locator.get_attribute: Timeout
10000ms exceeded` — which **replaces** the AssertionError that named the real
problem. The give-up path then reports the wrong subsystem, the exact failure
mode the readback existed to prevent.

## The fix, and that it already has a name in this repo

`automation/pages/pipeline_detail_page.py:32` defines
`DIAGNOSTIC_READBACK_TIMEOUT = 1000` for precisely this, added by PR #2091
(2026-09-09, reviewer-raised) and used at `:8254`. Pass it to every readback
made inside an `except` / give-up block.

## Why it is worth remembering

It **recurred one day later, in the same file**: the `#2077` port of PR #2058's
`close_versions_menu` / `close_version_selector` shape re-introduced the
unguarded form, because the port source (`agent_detail_page.py:2838`) predates
the constant. A ported shape inherits the source's gaps — when reviewing a
port, check the destination file for conventions the source never had.

Related: [[same_named_page_object_methods_are_decoys]]
