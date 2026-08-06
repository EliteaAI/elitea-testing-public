---
name: Catalog "Start Chat" needs an extra wait beyond open_agent_by_name()
description: Known defect #1043 — clicking Start Chat within ~200ms of modal-open silently no-ops; open_agent_by_name()'s own wait is insufficient, add page.wait_for_timeout(1000) before the click
type: feedback
---

`AgentHubPage.open_agent_by_name()`'s documented ready-signal (waits on the
modal's `GET .../public_application/prompt_lib/{id}` response AND
`modal_show_instructions_link` visible) is **NOT sufficient** to safely click
"Start Chat" right after — confirmed live on ELITEA-2368 with a scripted
repro matching the project's own pytest fixture context (fresh no-cookie
browser context, same as `conftest.py`'s `context` fixture):

- ≤200ms between modal-open and the Start-Chat click: **0/3** navigations
  succeeded (`PAGEERROR: Cannot read properties of null (reading
  'version_details')`, modal stays open, no exception surfaces to the test).
- ≥300ms: **3/3** succeeded.
- Reproduced identically for two different agents (ids 31 and 172) — root
  cause is generic (`AgentModal.jsx`'s `onStartConversation` reads
  `agentDetails.version_details.*` from a `useState(null)` that commits on
  a LATER render tick than the network response Playwright already awaited).

Already tracked as [EliteaAI/elitea-testing-public#1043](https://github.com/EliteaAI/elitea-testing-public/issues/1043)
(explicitly lists ELITEA-2356/57/58/59/60/61/62/68/69 as affected siblings —
check that list before filing a new issue, just comment with your occurrence).

**Fix for any case that opens a Catalog agent modal and clicks Start Chat:**
add `page.wait_for_timeout(1000)` immediately before
`agent_hub.click_start_chat()`, with a comment citing #1043. No DOM signal
distinguishes "agentDetails loaded" from "still null" for a no-starters agent
(both render identical empty-state text), so a fixed wait is the documented,
declared workaround — not defect masking.

## Addendum (ELITEA-2369): the SAME `agentDetails`-not-yet-committed race also empties the modal's CHAT STARTERS section — not just the Start Chat click

`AgentModal.jsx`'s CHAT STARTERS section reads
`agentDetails?.version_details?.conversation_starters` — ONLY the async
fetch state, no synchronous `agent`-prop fallback. Reading the section
immediately after `open_agent_by_name()` returns (which waits on the
network response + `modal_show_instructions_link` visible — NEITHER is
sufficient here, `modal_show_instructions_link` renders unconditionally)
can read a false "No predefined chat starters – just type your request to
begin." empty state for an agent that DOES have starters configured
(confirmed live: `AgentHubPage.get_modal_starter_items()` returned 0 for
"API Testing Buddy", which the API confirms has 4). Welcome Message text
comes from the same `agentDetails` state, committed together, so it's
equally affected.

**Fix for any case reading the modal's CHAT STARTERS or Welcome Message
sections:** wait for a REAL starter item (or non-empty welcome text) to
render before reading — e.g. `AgentHubPage.get_modal_starter_items().first
.wait_for(state="visible", timeout=...)` — rather than trusting
`modal_show_instructions_link`'s visibility alone. (For a genuinely
no-starters agent, this wait doesn't apply — that case asserts the
empty-state copy directly, as ELITEA-2368 already does.)
