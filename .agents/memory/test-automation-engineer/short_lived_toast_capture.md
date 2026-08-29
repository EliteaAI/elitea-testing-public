---
name: Short-lived toast capture (Elitea)
description: Success toasts live 3 s — MCP round-trips miss them; assert right after the driving response, or use a MutationObserver when exploring.
type: feedback
aliases: [toast, toast-alert, toast-message, snackbar, success confirmation]
tags: [area/ui, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## The fact

`src/common/constants.js` → `TOAST_DURATION_DEFAULTS`: **success/info 3000 ms**,
warning 7000, error 10000. The product-wide toast (`src/components/Toast.jsx`)
carries pre-existing testids `toast-alert` (+ `data-severity`), `toast-message`,
`toast-dismiss-button` — no testid work is ever needed for a confirmation.

## Why it bites

Driving the UI through Playwright MCP, **each click→evaluate pair costs >3 s**,
so three consecutive attempts to read a success toast all returned `null` — which
reads exactly like "the product shows no confirmation". It does show one.

## Two working responses

1. **Exploring (MCP):** install a DOM MutationObserver BEFORE the action and read
   its log afterwards:
   ```js
   window.__toastLog = [];
   new MutationObserver(() => document.querySelectorAll('[data-testid="toast-alert"]')
     .forEach(a => window.__toastLog.push({severity: a.getAttribute('data-severity'),
       msg: a.querySelector('[data-testid="toast-message"]')?.innerText})))
     .observe(document.body, {childList: true, subtree: true, characterData: true});
   ```
   (Transition frames log an empty `msg` — dedupe on the non-empty ones.)
2. **In a spec:** assert the toast in the step immediately after the driving
   response resolves, **before any table/list read**. It renders in the same tick
   the response lands, so this is deterministic — a couple of intervening reads
   is what outlives it.

Related: [[.agents/knowledge]] · surface digest `test-specs/settings-users-and-roles/_surface.md`
