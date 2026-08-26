---
name: Slash-mention MCP-only flow needs open_plus_menu param
description: add_mcp_participant_via_slash_menu() assumed the popper was already open (ELITEA-2203/2204 always call the Toolkit variant first) — an MCP-only test times out on mcps-menuitem unless it passes open_plus_menu=True.
type: feedback
---

## What happened (ELITEA-2205/2468 implementation)

`ChatPage.add_mcp_participant_via_slash_menu()` (added for ELITEA-2203) never
opens the plus menu itself — its docstring says "call this directly after
`add_toolkit_participant_via_slash_menu` (same open popper)". Its only prior
callers (ELITEA-2203, ELITEA-2204) always add a Toolkit participant first,
which calls `open_toolkits_submenu()` and opens the popper as a side effect.

ELITEA-2205/2468 is MCP-only (no Toolkit participant in the flow at all).
Calling `add_mcp_participant_via_slash_menu()` standalone times out waiting
for `mcps-menuitem` to become visible — the popper was never opened.

## Fix (additive, now shipped)

`add_mcp_participant_via_slash_menu()` gained an `open_plus_menu: bool =
False` parameter. When `True`, it clicks `plus_menu_button` first (same two
lines `open_toolkits_submenu()` uses). Default `False` preserves every
existing caller byte-for-byte — verified by re-running both prior callers
after the change (`test_slash_mention_toolkit_tool_selection.py`,
`test_slash_mention_toolkit_and_mcp_participants.py`): 2 passed, unchanged.

`select_slash_mention_toolkit()` also has (from ELITEA-2204's AFS caution,
now implemented) a `wait_for_first_tool: bool = True` param — pass `False`
for a zero-tools MCP/toolkit, otherwise the method's wait for the first
`slash-mention-tool-item-*` row to attach times out (no row ever attaches).

## Takeaway for the next slash-mention case

Before reusing `add_mcp_participant_via_slash_menu()` or
`select_slash_mention_toolkit()`, check the flow: MCP-only (no preceding
Toolkit participant call) → pass `open_plus_menu=True`. Zero-tools
toolkit/MCP → pass `wait_for_first_tool=False`. Both default to the
ELITEA-2203/2204 behavior, so an unmodified call only works for a
has-tools-Toolkit-then-MCP flow.
