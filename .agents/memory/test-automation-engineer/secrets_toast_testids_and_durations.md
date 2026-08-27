---
name: Toasts are testid-locatable app-wide, with severity-dependent lifetimes
description: toast-alert (+ data-severity) / toast-message exist on every toast; info+success vanish in 3s, so only a web-first expect() catches them
type: feedback
aliases: [toast, toast-alert, toast-message, snackbar, copied toast]
tags: [area/ui-handles, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The fact

`src/components/Toast.jsx` (shared, app-wide, pre-existing on `main`) carries
`data-testid="toast-alert"` **plus a `data-severity="{error|warning|success|info}"`
attribute**, and `data-testid="toast-message"` on the body text. Several older AFS/digest
notes on the Secrets surface claim "the toast has no testid, don't gate automation on it"
— that is wrong and superseded.

Lifetimes come from `TOAST_DURATION_DEFAULTS` (`src/common/constants.js`):
**error 10 s, warning 7 s, success 3 s, info 3 s.**

## Consequence

- Assert with a **web-first `expect(...).to_have_text(...)` attached immediately after the
  triggering click** — polling starts before the toast mounts. A one-shot `text_content()`
  loses the 3 s race (it did, live, in the ELITEA-2335 walk).
- When exploring by hand through MCP, an info/success toast will usually be **gone** by the
  time the next tool call lands; install a `MutationObserver` on `toast-message` first, then
  act, then read the log.
- Scope by severity with a class constant, never a raw handle:
  `TOAST_ALERT_SEVERITY = '[data-testid="toast-alert"][data-severity="{}"]'`
  (`agent_detail_page.py` is the existing precedent; `secrets_page.py` now has it too).

Related: [[playwright_mcp_cannot_read_clipboard_pytest_can]]
