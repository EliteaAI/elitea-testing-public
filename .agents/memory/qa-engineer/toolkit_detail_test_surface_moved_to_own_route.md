---
name: Toolkit Test Settings moved off the detail view to its own /test route
description: The toolkit TEST SETTINGS panel is no longer on /toolkits/all/{id} — it lives at /toolkits/:tab/:id/test, reached via the toolkit-test-button
type: project
aliases: [test settings panel, toolkit-test-button, toolkit-indexes-panel, toolkit-indexes-accordion, EL-5947, ToolkitTest route]
tags: [area/toolkits, type/ui-drift]
created: 2026-08-27
updated: 2026-08-27
---

## What changed (verified live 2026-08-27, localhost:5173, EliteaUI automation/testids @ 53bbab9a == origin/main @ cf648e9a)

The toolkit-detail redesign that once moved Indexes from a TAB into a Configuration-tab
ACCORDION has moved again. Two independent consequences, both confirmed against a
freshly-created Artifact toolkit:

1. **`toolkit-indexes-accordion` no longer exists on any EliteaUI ref** (deliberate UI-team
   removal, tracked as elitea-testing-public#1616). The Indexes surface is now a right-hand
   **side panel** inside the Configuration tab: `IndexesPanel.jsx`, root
   `data-testid="toolkit-indexes-panel"`, rendered by `ConfigurationTab.jsx` when the
   toolkit's schema exposes index tools.
   ⚠️ On a toolkit with **no PgVector/Embedding Model** configured, the panel renders only
   its "Indexing is not available" banner — `toolkit-indexes-count`,
   `toolkit-indexes-add-button` and `toolkit-indexes-empty-state` are ALL absent at runtime
   even though they exist on `main`. Only `toolkit-indexes-panel` is safe there.
2. **The whole TEST SETTINGS surface left the detail view.** `EditToolkit.jsx`'s `tabs`
   array now has exactly one entry (Configuration). The Test surface is its own route,
   `/toolkits/:tab/:toolkitId/test` (`RouteDefinitions.ToolkitTest`), a two-column
   "Test Settings | Results" panel. Reach it by clicking
   `data-testid="toolkit-test-button"` in the detail view's action bar (disabled while the
   form is dirty). Every testid inside it survived the move unchanged
   (`toolkit-test-empty-tool-select`, `toolkit-test-tool-select`,
   `toolkit-test-run-tool-button`, `toolkit-test-param-{key}`, `chat-message-list`).

## Traps

- **The run button's LABEL is now "Run Test", not "RUN TOOL"** — testid unchanged, so only
  step text / docstrings mislead.
- **`model-selector-button` does NOT render here.** `ToolkitTestSettings.jsx` uses
  `LLMModelSelector variant="field"`, whose early return emits only `model-selector-name`.
  Any `if model_selector_button.count() > 0` guard silently takes its fallback branch.
- **The Results column renders nothing before the first run**
  (`ToolkitTestResults.jsx: if (!messages.length) return null`), so `chat-message-list` does
  not exist pre-run and there is no welcome message any more.
- The result now sits inside a collapsed `chat-answer-thought-accordion`; `textContent`
  still reads through it, so `.text_content()`-based waits are unaffected — `.inner_text()`
  would NOT be.
- MCP siblings were already migrated (`/mcps/all/{id}/test`); the toolkit-side ones were not.

Related: [[project_briefing]]
