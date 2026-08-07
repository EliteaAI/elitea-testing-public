---
name: Chat Modules panel — "Ask User" 8th toggle added
description: Modules panel now renders 8 toggle switches (not 7) — new "Ask User"/ask_user between Python Sandbox and Swarm Mode
type: feedback
---

Live-confirmed 2026-08-07 (ELITEA-2464 work, localhost:5173 / `automation/testids`):
the Chat `+` → Modules panel now shows **8** toggle switches, not the 7 that
ELITEA-2162's original analysis (2026-08-03) and both cases' text describe.

New entry: **"Ask User"** (`data-testid="modules-toggle-ask_user"`, tool key
`ask_user`), positioned between "Python Sandbox" (`pyodide`) and "Swarm Mode"
(`swarm`) in DOM order:

1. `image_generation` — Image creation
2. `data_analysis` — Data Analysis
3. `internal_mcp` — Agents & Pipeline Builder
4. `planner` — Planner
5. `pyodide` — Python Sandbox
6. **`ask_user` — Ask User (NEW)**
7. `swarm` — Swarm Mode
8. `lazy_tools_mode` — Smart Tool Selection

`ChatPage.MODULE_TOGGLE_ORDER` in `automation/pages/chat_page.py` now has this
8th entry (additive insert in live DOM position). Any assertion elsewhere that
hardcodes "7 modules" (case text, docs, a future AFS) is now stale — check
`MODULE_TOGGLE_ORDER`'s live length before trusting a written "7". Filed as
clarification: EliteaAI/elitea-testing-public#1293.

Also confirmed: `ChatPage.get_open_plus_menu_item_count()` is scoped to the
`-menuitem` testid SUFFIX (`PLUS_MENU_ITEM_SUFFIX`) and does **not** match
`chat-attach-menuitem-button` (ends `-menuitem-button`, a different naming
convention for that one control) — it returns 5 for the plus-menu's 6 visible
top-level items (Attach Files is the odd one out), not 6. Don't assume it
counts every visible plus-menu item; verify each item's testid suffix before
trusting the helper's count.

Also confirmed: the toast's `data-severity` attribute lives on the
`toast-alert` testid (the MUI `Alert` root), NOT on `toast-message` (a plain
text `Box` child with no severity attribute of its own). Use
`ChatPage.get_toast_alert(severity)` / `TOAST_ALERT_SEVERITY` for a severity
assertion — asserting severity via `toast_message` silently asserts nothing
(the attribute isn't there).
