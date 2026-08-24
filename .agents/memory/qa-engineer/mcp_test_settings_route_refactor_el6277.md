---
name: MCP/Toolkit Test Settings became its own route (EL-6277) and lost its header controls
description: Test panel moved to /mcps/all/{id}/test as a 2-column split; clear-chat + fullscreen removed, run-history relocated to the detail action bar
type: project
aliases: [test settings panel, ToolkitTestPanel, TestTools.jsx, EL-6277, clear the chat mcp, fullscreen mcp test]
tags: [area/mcp, area/toolkits, type/product-change]
created: 2026-08-24
updated: 2026-08-24
---

## What changed

`EliteaAI/EliteaUI@cb030b7d` (`feat: [EL-6277] move indexes into the details right
panel`, #803, **2026-08-20**) deleted `TestTools.jsx` and replaced it with
`src/[fsd]/features/toolkits/ui/toolkit-test/ToolkitTestPanel.jsx`.

- The Test surface is a **ROUTE** now: `/mcps/all/{id}/test`, reached from the
  detail **action bar** via `toolkit-test-button`. It is no longer a right-hand
  region of the detail page.
- Layout is a **two-column split** — `Test Settings` | `Results`, both visible at
  once. Results no longer replace the settings form; there is no back-arrow.
- **Both column headers are plain `Typography` with no buttons.**

## The header-control trio the old cases describe

Pre-EL-5947 `TestTools.jsx@0cff136d^:191,195,196` rendered `FullScreenToggle`,
`ClearChatButton`, `ViewRunHistoryButton` in the panel header. Then:

| Control | Fate |
|---|---|
| Clear the chat | removed by `EL-5947` (@0cff136d, 2026-07-30) → back-arrow → removed entirely by EL-6277. `handleClearChat` still exposed by `useToolkitTestRunner`, consumed by nothing. |
| Fullscreen mode | removed by `EL-5947`, never returned. `FullScreenToggle.jsx` still wired on Skill / Index / Applications surfaces — and has **no testid** anywhere. |
| View run history | **relocated** to the detail action bar (`ToolkitForm.jsx:562`), testid `pipeline-history-tab`. |

## Why it matters

ELITEA-1938 (clear chat) and ELITEA-1939 (fullscreen) are `blocked` because their
subject was removed — clarifications #1725/#1726. ELITEA-1940 (run history) is
`ready-for-automation` — #1727 covers the location drift only.

**Before filing "control X missing" on this surface, check the table above.** The
removal is deliberate product work, so it is `question`+`case-text-drift`, NOT a
`bug` — unlike the sibling #1363, where the pipeline fullscreen toggle was never
implemented at all.

Related: [[toolkit_test_button_disabled_while_form_dirty]] · full detail in the
committed digest `test-specs/mcp/_surface.md` § Test Settings is now its own ROUTE.
