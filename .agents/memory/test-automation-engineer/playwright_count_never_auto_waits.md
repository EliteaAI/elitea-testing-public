---
name: Playwright .count() never auto-waits — a get_*_count() on a lazily-loaded list is a latent race
description: Never assert on a bare .count() of a lazily-loaded list; wait on .first before counting
type: feedback
---

`Locator.count()` is a **synchronous sample**. Playwright's auto-waiting applies
to actions and to web-first assertions (`expect(...).to_have_count(n)`), **not**
to `.count()`. So a page-object `get_<x>_count()` that a test asserts `> 0` on
reads whatever is in the DOM at that instant — green whenever the data happens
to be warm, red on a cold first open. It is a latent race that survives review
because the shape looks innocent.

The tell: the list is populated by a request that starts **on the interaction
that opens the container**, and the container renders synchronously and empty.
`ToolMenu.jsx` (`forceSkip = !mcpOpened.current` into `useLibraryToolkits`) is
the canonical in-repo instance — the "+ MCP" popper opens with `items = []` and
only fetches on the first click. Measured window: ~0.56 s on dev.elitea.ai,
~1.9 s on localhost; the second open in the same browser context is instant
(RTK Query cache), which is why a warm/repeated reproduction looks green and
why "ran it 4× standalone, no fix needed" is the wrong conclusion here.

**Fix shape** — an additive `wait_for_*_items()` page-object method that waits
on the row testid before the count is taken:

```python
popper.locator(self.TOOLKIT_MENU_ITEM_SELECTOR).first.wait_for(state="visible", timeout=timeout)
```

Do **not** fold the wait into the `get_*_count()` itself: it changes the
semantics of every merged call site and hangs (instead of returning 0) on a
case that legitimately asserts an empty list.

Corollary worth remembering: if the *select* path on the same list never flaked
while the *count* path did, that asymmetry is the diagnosis, not a coincidence
— `Popper.select_menuitem_by_testid` (`components/mui.py`) already does the
`wait_for(state="visible")` the count path was missing.

Loading/empty placeholders in `UnifiedDropdown.jsx` carry **no testid**, so
"wait for Loading to disappear" is not expressible; waiting for the first real
row is the only handle that exists on `main`.

(Established ELITEA-1955 / issue #1890, 2026-08-28. Sibling specs
`test_pipeline_mcp_node_fresh_attach.py` and
`test_pipeline_tools_section_mcp_add_view_remove.py` carry the same race under
cards #1891/#1892.)
