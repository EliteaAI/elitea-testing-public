---
name: Shared-component testid prop — check EVERY call site before deriving it from a flag
description: A shared component's `isMCP ? testid : undefined` renames the testid on every surface that renders it, not just yours.
type: feedback
aliases: [chipTestIdPrefix, titleTestId, CategoryFilter, ToolkitTypeSelector, category-filter-tab, shared component testid]
tags: [area/testids, type/regression-risk]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

An AFS work order for a shared component (`src/components/`, `src/[fsd]/shared/`) will
typically say "add a `xTestId` prop, plumb it through, and pass it only when `isMCP`".
Putting the `isMCP ? … : undefined` **decision inside the intermediate component** looks
identical to putting it at the page's call site — until you find that component has more
than one caller.

Concrete instance (ELITEA-1949, 2026-08-24): `src/pages/Toolkits/ToolkitTypeSelector.jsx`
is rendered by **two** call sites that both pass `isMCP`:

- `src/pages/Toolkits/CreateToolkit.jsx` — the standalone `/mcps/create` page
- `src/[fsd]/features/chat/ui/editors/ToolkitEditor.jsx:304` — the **in-chat MCP canvas**

Deriving `chipTestIdPrefix` from `isMCP` inside `ToolkitTypeSelector` renamed the canvas's
category chips from `category-filter-tab` to `mcp-type-picker-filter-chip-*`, silently
breaking two merged specs (`tests/ui/chat/test_create_mcp_from_conversation.py`,
`…_discard_changes.py`, via `McpFormPage.select_remote_category_tab`). Caught before
committing only because the page object's own docstring named the canvas caller.

## The check (one command, before you edit)

```bash
cd ../EliteaUI && grep -rn "<ComponentName" src | grep -v "src/.*/ComponentName.jsx:"
```

Then, for each call site found, decide whether it should get the new testid. **Hoist the
`cond ? testid : undefined` to the call site that wants it** and make the intermediate
component a pure forwarder. Keeping the old generic testid as a no-prefix fallback is NOT
enough on its own — the fallback only protects callers that don't pass the prop.

## Evidence discipline

This is a shared-caller change, so the additive-only rule applies: enumerate the affected
specs, re-run them, and name them + their verdict in the PR description.

Related: [[additive_only_grep_scope_your_own_unmerged_commits]]
