---
name: Toolkit Test Settings moved to its own /test route (#1616 redesign)
description: Test Settings left /toolkits/all/{id}; reach it via toolkit-test-button. Layout flipped to LEFT column, breaking x>700 panel filters.
type: project
aliases: [toolkit test settings, toolkit-test-empty-tool-select, open_test_surface, toolkit-test-button, Run Test, /toolkits/test route]
tags: [area/toolkits, type/ui-drift]
created: 2026-08-27
updated: 2026-08-27
---

## What changed

The #1616 toolkit redesign moved the whole TEST SETTINGS surface **off** the toolkit detail
view (`/toolkits/all/{id}`) and onto its own route:

- `src/routes.js` → `ToolkitTest: '/toolkits/:tab/:toolkitId/test'` → `[fsd]/pages/toolkit/ToolkitTest.jsx`
- The product's own route in is the detail action-bar **Test** button,
  `data-testid="toolkit-test-button"` (`ToolkitForm.jsx`), disabled while the form is dirty.
- On `/toolkits/all/{id}` the whole `toolkit-test-*` family, `chat-message-list` and the
  literal text "Test Settings" are **all absent**. The testids were never removed or renamed —
  so a testid-presence grep says "on main ✓" while every locator times out. **This drift class
  cannot be diagnosed by a promotion-gap grep; only a live DOM read finds it.**

Reusable repair already on `origin/main`: `ToolkitDetailPage.open_test_surface()`
(`automation/pages/toolkit_detail_page.py`, commit `c25113893`) — clicks the button and waits
for `.*/toolkits/[^/]+/\d+/test`. **Never `page.goto()` the `/test` URL**: forcing it
substitutes the navigation (`.agents/testing.md` § Fidelity policy).

## The layout flipped — watch for x-coordinate panel filters

`ToolkitTestPanel.jsx` renders **Test Settings on the LEFT**, Results on the right. Any helper
that disambiguated "the right panel" by bounding box now matches nothing. Worked example:
`_fill_test_settings_param()`'s `bb["x"] > 700` filter — the Confluence `Label` input measures
**x = 350** at viewport 1728 (less at the suite's 1366 headless viewport), so the helper hit its
`if target is None:` branch and **silently returned without filling**, leaving `Run Test`
disabled. A silent no-op surfaces as a timeout one step LATER, at a different symptom.

## Stable handles on the new surface (all on EliteaUI `main`, verified 2026-08-27)

| What | Handle |
|---|---|
| Route in | `toolkit-test-button` |
| Empty state (before a tool is chosen) | `toolkit-test-empty-tool-select` |
| Tool combobox (panel, after a tool is chosen) | `toolkit-test-tool-select` |
| Dropdown option | `select-option-{tool_schema_key}` |
| Param wrapper / input | `toolkit-test-param-{key}` / `toolkit-test-param-{key}-input` |
| Run button (label "Run Test") | `toolkit-test-run-tool-button` |
| Result list (absent until the first run completes) | `chat-message-list` |

`ToolkitConfig.test_tool_result_indicator` **is** the tool's schema key, so
`select-option-<indicator>` and `toolkit-test-param-<key>` can be derived from config —
verified for `list_branches_in_repo`, `list_projects`, `list_pages_with_label`. Numeric params
(GitHub's `Max Count`) carry **no** testid; the string/boolean/anyOf renderers do.

## `✅` is not a success oracle

The result marker means "the tool executed", not "the call succeeded". GitHub returned
`✅ list_branches_in_repo (0.213s)` with a `401 Bad credentials` body. Assert the expected
**content** in the result text; never substitute the ✅ marker for it.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
