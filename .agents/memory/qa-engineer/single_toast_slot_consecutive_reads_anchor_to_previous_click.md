---
name: Single toast slot — consecutive toast reads anchor to the previous click
description: Two toast-producing clicks in a row — a one-shot toast read after the 2nd click returns the 1st toast; demand a retrying expect on THIS click's text
type: feedback
aliases: [toast race, get_toast_text stale, replace-in-place toast, toast-message stale read, copy toast mismatch]
tags: [area/toast, type/review-check, status/verified]
created: 2026-09-16
updated: 2026-09-16
---

## The mechanism (verified in EliteaUI source, origin/main == automation/testids, 2026-09-16)

- `src/components/ToastProvider.jsx` keeps ONE `toastProps` state; `openToast` does
  `setToastProps({open:true, severity, message})` — overwrite in place, no queue, no drop.
- `src/components/Toast.jsx` renders one MUI `Snackbar`; `toast-alert` / `toast-message`
  stay mounted and only `{message}` changes.
- `CopyToClipboardButton.jsx` fires `toastInfo(copyMessage)` AFTER `await writeText()`.
- MUI `useSnackbar.js` auto-hide effect deps are `[open, autoHideDuration]` — a message swap
  while `open` stays true does NOT restart the 3 s timer (info default; env-overridable via
  `INFO_TOAST_DURATION`). The 2nd message inherits the 1st toast's remaining window.

So after click #2, the toast node is already visible with click #1's text. A one-shot
`wait_for(visible)` + `text_content()` read (`get_toast_text()` on 4 page objects,
17 call sites in tests/, 5 files with 2 calls) is anchored to the PREVIOUS click —
CI red #2321 on ELITEA-2056, `got: 'The ID has been copied…'` at the Version-ID step.

## Reviewer check

For any spec with two toast-producing actions in sequence: the read after the second
action must be an auto-retrying `expect(page.toast_message).to_contain_text(<this
click's text>)`, AND the two expected strings must not be substrings of each other
(check with `a in b`/`b in a`); otherwise a stale read satisfies the assertion.
Waiting for the first toast to DISMISS is unnecessary (replace, never drop) and slower.
Residual window: 3 s minus (toast #1 open → click #2) — a false RED needs ~2.5 s of
stalls in that gap; no timeout raise fixes it (the toast is gone, not slow).

Related: [[a_positive_assertion_guarding_an_absence_only_by_ordering_is_fragile]]
