# Support Assistant Surface Digest

**Last updated:** 2026-08-18 (ELITEA-2420 analysis)

## Confirmed Handles

| Element | Handle | Confirmed | Notes |
|---|---|---|---|
| Launcher button | `button[aria-label="Support Assistant"]` | 2026-08-18 | Opens widget; requires JS-evaluate click (MUI overlay gotcha) |
| Widget title | `.elitea-assistant-header-title` or `h2:has-text("ELITEA Support")` | 2026-08-18 | Widget open indicator |
| Attach button | `button[aria-label="Attach file"]` | 2026-08-18 | Opens file chooser (click-to-browse) |
| Send button | `button[aria-label="Send message"]` | 2026-08-18 | Disabled until input/attachment; enables on either |
| Messages container | `.elitea-assistant-messages` | 2026-08-18 | Conversation history |
| Input row | `.elitea-assistant-input-row` | 2026-08-18 | Contains attach + input + send |
| File input (hidden) | `input[type="file"]` | 2026-08-18 | Hidden input; triggered by attach button click |

## Known Quirks

**Drag-and-drop NOT implemented (defect #1583):** The widget has no drag-drop handlers. All drop attempts fail with "dragover handler did not call preventDefault()". Click-to-browse (Attach button) works perfectly.

**Launcher click requires JS-evaluate:** Per project briefing, the launcher (and other MUI-overlay-guarded buttons) fails with `browser_click`. Use `browser_evaluate` with `el => el.click()` pattern.

**Connected first-party package:** Support Assistant ships as `@eliteaai/elitea-assistant`, source in `../elitea_assistant` sibling repo. Testids are added in THAT repo's `automation/testids` branch (`.agents/workflow.md` § Connected repos). Current handles are `aria-label`-based; future tests should add testids per connected-repo discipline.

**File acceptance:** Click Attach button → native file chooser opens → select file → attachment chip appears with file name + Remove button → Send button enables.

**Message submission:** Send button click submits message; AI response arrives via WebSocket (~2s delay). User message body may render empty initially (observed in ELITEA-2420 run); AI response starts with "Echo: " prefix.

## Scope

Support Assistant widget is a floating chatbot accessible from any page (persistent across navigation). Tests at `/chat` but widget behavior is global.
