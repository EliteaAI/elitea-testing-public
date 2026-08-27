---
name: buildErrorMessage returns Unknown error for every transport failure
description: RTK-Query FETCH_ERROR misses every branch of EliteaUI's shared buildErrorMessage, so offline/network failures toast a bare "Unknown error" app-wide
type: project
aliases: [Unknown error toast, network failure message, offline error, FETCH_ERROR]
tags: [area/errors, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## The fact

`src/common/utils.jsx:146-184` (`buildErrorMessage`) branches on `originalStatus === 404`,
`status === 403`, `data.message`, `data.error`, `data.errors`, and array `data`. An RTK
Query transport failure is `{ status: 'FETCH_ERROR', error: '...' }` — **no numeric
status, no `data` at all** — so every branch misses and it falls through to
`return typeof err === 'string' ? err : err?.data;` → `undefined`, which the toast
provider renders as the default **`Unknown error`**.

It is a **shared** helper, so this is app-wide, not a Secrets quirk. Filed as bug
**#1910** while working ELITEA-2349.

## Why it matters when writing a test

Do **not** assert the literal `Unknown error` string as the expected contract — that
encodes a defect and goes red the day the product improves the message. Assert the
**shape** the case actually asks for: an error-severity toast
(`toast-alert` + class `MuiAlert-colorError`), non-empty `toast-message`, and no stack
trace in the toast text or the page body (`TypeError` / `Uncaught` / `at Object.` /
`.jsx:` / `.js:` / `    at `).

Toast handles, all on `main`: `toast-alert` (`src/components/Toast.jsx:60`),
`toast-message` (`:74`), `toast-dismiss-button` (`:71`). Error toasts do not fast
auto-hide (still up after 10 s) and clear on a successful refetch.

Related: [[elitea_roles_are_project_scoped]]
