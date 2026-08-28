---
name: UnifiedDropdown popper first-open load race
description: "+ MCP"/"+ Toolkit" popper rows arrive ~0.5-1.9s after the click; count() sees zero. Wait on toolkit-menu-item.
type: feedback
aliases: [toolkit-menu-item empty, "+ MCP popper empty", UnifiedDropdown loading, get_mcp_popper_menu_item_count, ToolMenu forceSkip]
tags: [area/pipelines, area/agents, type/flake]
created: 2026-08-28
updated: 2026-08-28
---

## The race

`ToolMenu.jsx` passes `forceSkip = !mcpOpened.current` into `useLibraryToolkits`, so
RTK Query's toolkit-list request is **skipped until the "+ MCP"/"+ Toolkit" button is
first clicked** — the request starts at click time. The popper opens synchronously
(`open={Boolean(anchor)}`) with `items = []`.

`UnifiedDropdown.jsx` then renders, in order:
- `isLoading` → a disabled `MenuItem` reading `Loading...` — **no testid**
- `!isLoading && items.length === 0` → a disabled `MenuItem` (`No mcps available`) — **no testid**
- rows → `data-testid="toolkit-menu-item"`
- the search `TextField` (`toolkit-search-input`) is present from the **first frame**

So `toolkit-search-input` passes immediately while `toolkit-menu-item` is zero.

## Measured (2026-08-28)

`GET /api/v2/elitea_core/tools/prompt_lib/{project}?query=&sort_by=name&sort_order=asc&mcp=true&limit=50&offset=0`
fires at +22 ms, 200 at +325 ms, rows visible at **~540 ms on dev.elitea.ai** and
**~1900 ms on localhost:5173** (localhost is SLOWER). Second open in the same context
is instant — RTK Query cache. **The race is first-open-only**, which is why warm or
repeated standalone runs look green and why "ran it 4/4 standalone, no fix needed"
(issue #1776) was a wrong conclusion.

## The fix shape

Playwright's auto-waiting does NOT apply to `.count()`. Wait on the row testid before
counting:

```python
popper.locator('[data-testid="toolkit-menu-item"]').first.wait_for(state="visible", timeout=10000)
```

`Popper.select_menuitem_by_testid` (`components/mui.py`) already does exactly this —
which is why the *select* step never flaked while the *count* step did. Never a fixed
`wait_for_timeout` (`AgentDetailPage.add_mcp()`'s `wait_for_timeout(1000)` is pre-existing
tech debt, not a pattern). "Wait for Loading to disappear" is not expressible: neither
placeholder carries a testid on `main`.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
