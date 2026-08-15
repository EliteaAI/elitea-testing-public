---
name: MCP browser_run_code_unsafe loses in-page editor state between separate calls
description: Chat folder/conversation inline-edit mode doesn't survive across two browser_run_code_unsafe invocations — do the whole open-editor-then-assert flow in ONE script call.
type: feedback
---

Live-driving the chat folder rename editor (or any inline MUI edit-mode UI)
via `mcp__playwright__browser_run_code_unsafe` in SEPARATE tool calls does
NOT preserve the open-editor state between calls, even though the underlying
Playwright `page`/browser session itself persists (navigating back to
`/chat` in a later call shows the same folder list, same auth). Observed
twice this session (ELITEA-2124/2125/2126/2131, chat-remaining-w06):
opening a folder's rename editor in one `browser_run_code_unsafe` call, then
querying `[data-testid="chat-folder-name-input"]` in the NEXT call, times out
at 30s waiting for the input to exist — the editor had silently closed
between calls (likely the folder-list's own periodic refetch/re-render
unmounts `FolderItem.jsx`'s edit-mode local state).

**Also note:** the accessibility-snapshot `ref=` values returned by
`browser_snapshot`/`browser_find` go stale within roughly one tool-call
round-trip on this page specifically (repeated "does not match any
elements" errors even immediately after a fresh snapshot) — consistent with
a live status-polling component (`status [ref=...]`) re-rendering the tree.
Prefer testid-scoped `page.locator()` calls inside `browser_run_code_unsafe`
over ref-based `browser_click`/`browser_type` on this surface.

**Fix:** when the exploration needs multiple sequential interactions against
an open inline editor (type → assert → click → assert → type again → ...),
write ONE `browser_run_code_unsafe` script that does the ENTIRE
seed → open-editor → interact → assert → cleanup sequence, rather than
splitting it across several tool calls. Also use `MUI`-safe field clearing
(`input.click()` + `waitForTimeout(100)` + `input.clear()` +
`waitForTimeout(100)` + `pressSequentially()`, matching `ChatPage.set_folder_name()`'s
own documented pattern) — a bare `Control+a`+`Backspace` without the waits
reproduced the project's own documented "append not replace" race
(`"W06GapCheck4New folder"` observed live) on the FIRST attempt.
