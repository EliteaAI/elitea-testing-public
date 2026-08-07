---
name: Run History list rows show Date/Version/Duration, never a conversation preview
description: RunHistoryListItem.jsx renders 3 fixed columns; TMS case text sometimes expects a first-message/title preview per row that does not exist
type: project
---

Agent (and Pipeline/MCP/Toolkit) detail pages' Run History panel
(`RunHistoryContainer.jsx` → `RunHistoryList.jsx` → `RunHistoryListItem.jsx`)
renders each row as exactly three columns — **Date** (`dd-MM-yyyy, hh:mm a`),
**Version**, **Duration** — via `RunHistoryTooltipCell`. `RunHistoryList.jsx`'s
`tableHeaderItems` literally is `['Date', 'Version', 'Duration']` (Version
omitted only when `versions === null`, e.g. some Toolkit/MCP sources).

**There is no conversation preview / first-message / title text anywhere in the
row.** That content only renders in the right-hand `RunHistoryChat` panel
*after* a row is clicked. If a TMS case describes each Run History entry as
showing "a preview of the conversation (first message or title)" (ELITEA-1876
did), that is case-text drift describing a different, ChatGPT-sidebar-style
design — not a product defect (reverse-masking guard). Filed as clarification
`EliteaAI/elitea-testing-public#1282`.

All three columns are readable via the row's own `text_content()` /
`all_text_contents()` on the existing `run-history-list-item` testid — no new
per-cell testid is needed to assert them.

Separately: the earlier-reproduced `EliteaAI/elitea-testing-public#1093` ("no
UI way to close Run History") appears FIXED as of 2026-08-06 —
`RunHistoryContainer.jsx` now renders a working `aria-label="close run
history"` button when `onClose` is passed. Verify live before trusting either
digest note or memory — it may have been in-flight when #1093 was filed.
