---
name: MUI accordion collapse hides children, it does not unmount them
description: Collapsed BasicAccordion sections stay in the DOM behind visibility:hidden — assert not_to_be_visible(), never to_have_count(0)
type: feedback
aliases: [accordion collapse assertion, BasicAccordion testid, MuiCollapse-hidden, aria-controls collision]
tags: [area/ui-handles, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

EliteaUI has **two different hide mechanisms on the same page** (`/settings/memory`), and
using the wrong assertion passes or fails for the wrong reason:

| Mechanism | Where | Correct assertion |
|---|---|---|
| Accordion **collapse** (MUI `Collapse`) | any `BasicAccordion` section header | `not_to_be_visible()` |
| **Conditional unmount** (`{isEnabled && …}`) | `context-management-toggle` turning its children off | `to_have_count(0)` |

Verified live 2026-08-28: with `CONTEXT MANAGEMENT` collapsed,
`[data-testid="max-context-tokens-input"]` still returns **count 1**. The
`MuiCollapse-root` carries `MuiCollapse-hidden`, `height: 0px` and **`visibility: hidden`**,
so `element.checkVisibility()` is `false` and Playwright honours it.

## `BasicAccordion` handles (src/[fsd]/shared/ui/accordion/BasicAccordion.jsx)

- `data-testid` prop → the wrapper `<Box>` (lines 40, 45) — e.g. `context-management-section`.
- per-item **`testId`** → the `StyledAccordionSummary` (line 70), i.e. the **clickable header**
  carrying `aria-expanded`. This is the handle to request for any collapse/expand case;
  pure prop plumbing, no new DOM node.
- `defaultExpanded` defaults to **`true`** — sections that never pass the prop are still
  expanded on load.
- ⚠️ `aria-controls` is `panel-content-${index}` **per item**; one-item accordions all share
  `panel-content-0`. Never key a locator on it.

Related: [[personalization_page_does_not_exist]]
