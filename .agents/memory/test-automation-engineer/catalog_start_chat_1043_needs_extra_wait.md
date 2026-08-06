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
