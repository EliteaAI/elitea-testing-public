---
name: MUI Popper .first can resolve to a Tooltip, not the dropdown you opened
description: A MUI Tooltip root is also .MuiPopper-root and portals to body; `.first` (and `:visible`) can return it instead of the dropdown.
type: feedback
aliases: [MuiPopper-root nth=0, Select LLM Model tooltip, popper nth 0, toolkit-search-input assert 0 > 0]
tags: [area/ui-locators, type/flake-rootcause]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`components.mui.Popper.wait_for()` resolves `page.locator(".MuiPopper-root").first`.
A MUI **Tooltip** root carries `MuiPopper-root MuiTooltip-popper MuiTooltip-popperInteractive`
and portals to `<body>`, so a tooltip already open when a dropdown opens sorts at `nth=0`.
Symptom: `popper.is_visible()` passes, `popper.locator('[data-testid="…"]').count() == 0`,
message ends `selector='.MuiPopper-root >> nth=0'`.

**`:visible` does NOT fix it** — the tooltip is visible too, and `:visible` preserves DOM order.
Measured on the pipeline detail page: `visible-count=2`, `.first` still the tooltip.
Working discriminators: `.MuiPopper-root:not(.MuiTooltip-popper)` or
`.MuiPopper-root:has([data-testid="…"])`. `.last` works but is not guaranteed.

## Two triggers, both proven live

1. **Hover** the tooltip's anchor.
2. **Programmatic `.focus()`** — headless Chromium reports `:focus-visible === true` for a
   programmatic focus, which is exactly what MUI's `Tooltip` `onFocus` tests. **No hover needed.**

The overlap window is short (~a few hundred ms after the pointer leaves), so the assertion that
runs *immediately* after opening catches it while a later `select_*` call on the same locator
usually recovers — which makes it look like a flake when it is deterministic.

## Triage tell

Read the allure failure screenshot: if a tooltip is on screen, it is this bug, **not** the
EL-6351 lazy-load race (`toolkit-menu-item` arriving late). The two produce the same
`assert 0 > 0` shape. That is how a third spec was left unrepaired after PR #1921.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
