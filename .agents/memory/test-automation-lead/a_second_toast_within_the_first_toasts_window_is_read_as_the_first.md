---
name: A second toast within the first toast's window is read as the first — single-slot ToastProvider replace-in-place
description: EliteaUI has ONE toast slot; a one-shot wait_for(visible)+text_content() after a second toast-producing click resolves on the still-mounted previous toast; the honest fix is a retrying expect anchored to THIS click's text, not a dismissal wait or a longer timeout
type: feedback
aliases: [stale toast read, get_toast_text race, ToastProvider single slot, copy toast mismatch, consecutive toasts, ELITEA-2056 toast]
tags: [area/triage, area/flake-class, type/mechanism]
created: 2026-09-16
updated: 2026-09-16
---

## The signature (#2321, ELITEA-2056, DEV Stable #166)
`assert 'The Version ID has been copied…' in 'The ID has been copied…'` — Step 8 asserting the text
Step 7 produced. Reads like a product text change; it is not. Product strings unchanged on main
(`ApplicationInformation.jsx:86/:95`); the spec passed in the two prior nightlies that day.

## Mechanism (verified in source by implementer AND reviewer)
- `src/components/ToastProvider.jsx:13-21` — ONE `toastProps` state; `openToast` overwrites in place.
  No queue, no drop.
- `Toast.jsx` — one MUI Snackbar; `toast-alert`/`toast-message` stay mounted, only `{message}` swaps.
- `CopyToClipboardButton.jsx:15-18` — `toastInfo` fires only AFTER `await clipboard.writeText()`.
- MUI `useSnackbar.js:55-60` — auto-hide timer keyed on `[open, autoHideDuration]`, not `message`;
  `TOAST_DURATION_DEFAULTS.info = 3000` (env-overridable `INFO_TOAST_DURATION`).
⇒ after the 2nd click, `wait_for(visible)` + one-shot `text_content()` resolve on the 1st toast.
Empirically: expecting the Step 7 text at Step 8 PASSES by default — the old code only passed when the
React commit beat three Playwright round-trips.

## The fix shape (PR #2328) and the two wrong ones
- RIGHT: `expect(page.toast_message).to_contain_text(<THIS click's text>, timeout=TOAST_TIMEOUT)` —
  valid only when consecutive messages are not substrings of each other (check mechanically).
- WRONG: "wait for the first toast to close" — slower and unnecessary (nothing is dropped).
- WRONG: raise `TOAST_TIMEOUT` — the read is anchored wrong, not slow.
`get_toast_text()` stays correct for the FIRST toast on a page (~50 callers). Sibling exposure
(two reads in one test): 4 specs, tracked as #2329.

## Triage cost
Message-string grep on both refs (present on both ⇒ not a promotion gap) + product-string grep on
EliteaUI main + the two prior nightlies' PASS lines = disposition in ~5 min. Analyst slot skipped
(observable/expected unchanged); implementer + fresh reviewer only.
