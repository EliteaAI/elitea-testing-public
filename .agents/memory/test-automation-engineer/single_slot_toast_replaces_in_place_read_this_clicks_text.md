---
name: Single-slot toast replaces in place — read THIS click's text, never "a toast is visible"
description: Back-to-back toasts share one toast-alert node; anchor each read with a retrying to_contain_text on the click's own message
type: feedback
aliases: [toast race, toast-alert stale read, copy toast, ToastProvider single slot, get_toast_text race]
tags: [area/toast, type/flake-mechanism, status/verified]
created: 2026-09-16
updated: 2026-09-16
---

## Mechanism (from source, 2026-09-16)

- `EliteaUI/src/components/ToastProvider.jsx:13-21` — ONE `toastProps` state; `openToast`
  overwrites it in place. No queue, no drop. `ToastComponent` renders a single `<Toast>`.
- `Toast.jsx:52-58` — one MUI `Snackbar`; `toast-alert` / `toast-message` stay mounted while
  `open` is true, only `{message}` changes.
- `src/[fsd]/shared/ui/button/CopyToClipboardButton.jsx:15-18` — `toastInfo(copyMessage)` fires
  only AFTER `await navigator.clipboard.writeText()` resolves (tens of ms after the click).
- MUI `useSnackbar.js:55-60` — auto-hide timer keys on `[open, autoHideDuration]`, NOT
  `message`: a swapped-in second toast inherits the first toast's remaining window
  (`TOAST_DURATION_DEFAULTS.info = 3000`).

## Consequence

After a second toast-producing click, `get_toast_alert(sev).wait_for(visible)` +
`get_toast_text()` (one-shot `text_content()`) resolve instantly on the FIRST toast.
Verified on localhost (ELITEA-2056): expecting the previous click's text at the next step
**passes** on every poll-1 — the stale read is the default state, the old code only passed
when the clipboard promise + React commit beat three Playwright round-trips (CI DEV #166 lost).

## Correct shape

```python
pipeline_page.copy_version_id_button.click()
expect(pipeline_page.get_toast_alert("info")).to_be_visible(timeout=TOAST_TIMEOUT)
expect(pipeline_page.toast_message).to_contain_text(THIS_CLICKS_TEXT, timeout=TOAST_TIMEOUT)
```

Precondition for this to be honest: the expected texts of consecutive toasts must NOT be
substrings of one another (check before relying on it). No wait for the prior toast's
dismissal is needed — the second toast replaces, never drops; waiting would only burn ≤3 s.
`get_toast_text()` (`pipeline_detail_page.py:6635`, many callers) is fine for a FIRST toast
on a page; it is unsafe for any toast that follows another within its auto-hide window.

Related: [[a_settle_can_be_fragile_and_vacuous_at_once]] · [[grep_the_page_object_before_building_a_locator]]
