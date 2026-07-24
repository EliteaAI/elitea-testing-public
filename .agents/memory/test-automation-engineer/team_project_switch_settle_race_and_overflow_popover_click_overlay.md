---
name: Team-project switch settle race, and a residual MUI overlay after closing the attachment-overflow popover blocks the Send click
description: switch_project()'s own wait_for_network() can return before a staggered project-info enrichment batch settles, silently reverting the selection back to Private if the next action (e.g. create-conversation) fires too soon — poll the rendered label instead. Separately, closing the attachment "+N" overflow popover via Escape can leave a residual overlay over the Send button that swallows a coordinate-based click(force=True); use evaluate("el => el.click()") instead.
type: feedback
---

## ELITEA-2091 implementation (PR #1051)

Two distinct, live-confirmed quirks hit while writing
`test_create_conversation_team_project_attachments_and_llm_switch`
(`test_conversation_management.py`).

### 1. Project-switch settle race (reproducible, automation-speed only)

Sequence: `chat.switch_project("471")` → assert sidebar shows "Elitea Testing
Team" (passes) → `chat.click_create_conversation()` → assert again → **fails,
shows "Private"**. Confirmed via `page.on("response")` + reading
`sessionStorage.getItem('elitea_ui.project.id')`: right after
`switch_project()` returns, the app fires a STAGGERED batch of
`GET .../project_info/prompt_lib/{id}/project-info` requests (one per
recently-viewed project, enriching the sidebar's list) — NOT all in flight at
once. `switch_project()`'s own `wait_for_network()` (networkidle) can be
satisfied in a gap BETWEEN two of these staggered requests, well before the
whole batch resolves. If the conversation gets created before the batch
fully settles, the underlying reducer (a `projectList`/`authorDetails`
RTK-Query matcher, per `settings.js` source) resets the selected project back
to the personal/private one.

**Diagnosis discipline that worked:** an EXTRA bare `chat.wait_for_network()`
call did NOT fix it (returned instantly — the batch hadn't even started yet
in that specific timing). A raw `page.wait_for_timeout(4000)` DID fix it
2/2 — confirming a genuine settle window, not a permanent revert. Converted
that into a condition-based fix: `ChatPage.wait_for_selected_project_stable
(expected_substring, timeout, poll_interval, required_stable_reads)` — polls
`get_selected_project_text()` for N consecutive matching reads (same idiom as
the existing `wait_for_message_content_stable`). Added as a new ChatPage
method (additive), used right after `switch_project()` and before the next
action.

**Not filed as a product defect** — only reproduces at automation speed
(clicking through in milliseconds); a human wouldn't hit this window. Same
CLASS as the already-documented `save_networkidle_race_quirk.md`
(`networkidle` resolving between a click and a debounced/staggered
dispatch) — this is now the second confirmed instance of that pattern in
this codebase; treat "an extra `wait_for_network()` call didn't help" as a
signal to reach for a stability-poll, not a longer sleep.

### 2. Residual MUI overlay after closing the attachment overflow popover blocks Send

After Step 5 (drag-and-drop attach), `get_all_attached_file_names()` opens
the "+N" overflow popover (to read hidden filenames) and closes it via
`page.keyboard.press("Escape")`. Later, `chat.send_button.click(force=True,
timeout=...)` silently did nothing — `get_message_count()` stayed 0 and the
composer's text/attachments were UNCHANGED even 2s after the "click"
(confirmed via explicit before/after debug reads). `force=True` bypasses
Playwright's own actionability checks but still dispatches a coordinate-based
mouse event that the BROWSER routes to whatever's topmost at that pixel — a
residual overlay/backdrop from the just-closed MUI Menu, still occupying the
Send button's coordinates, silently absorbed the click instead.

**Fix:** `chat.send_button.evaluate("el => el.click()")` instead of
`.click(force=True)` for this specific call site — calls the DOM element's
`.click()` directly, bypassing paint-order/coordinate routing entirely.
Exactly the documented `mui-patterns.md` "MUI Overlay Interception" recipe
("Use `evaluate()` for Save buttons during streaming, critical actions") —
hadn't previously seen it trigger on the SEND button specifically, only after
an overflow-popover interaction immediately beforehand. `send_message()`'s
existing `force=True` click stays fine for every OTHER test (none of them
interact with the overflow popover right before sending).

## Generalization

Any test that (a) switches project then immediately creates/acts, or (b)
opens+closes a MUI popover/menu then immediately clicks a DIFFERENT control,
should treat "immediately after" as suspect. Prefer a stability-poll for (a)
and `evaluate("el => el.click()")` for (b) over adding more `wait_for_network()`
calls or longer sleeps — both are cheap, condition-based, and don't touch any
shared method with existing callers.
