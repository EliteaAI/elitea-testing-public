---
name: Artifacts multi-file upload — toast-capture technique + single-response gotcha
description: ELITEA-1826 — MutationObserver technique for verifying fast-dismissing toasts with exact-text assertions, and why click_upload_path_upload_button_and_capture_response() must not be used for multi-file uploads
type: project
---

## MutationObserver technique for verifying a fast-dismissing toast's exact text

`toast-message` (the app-wide success toast, `success_toast_message` on
`ArtifactsPage`) auto-dismisses fast enough that a single-shot DOM read after
an action can miss it entirely — ELITEA-1832 already documented this for the
*absence* case (asserting a toast did NOT appear). ELITEA-1826 needed the
*positive* case: proving a toast appears with an EXACT expected string
("Your file(s) have been successfully uploaded!").

A single post-click snapshot is unreliable in both directions: it can read
"absent" either because the toast never fired, or because it fired and
fully dismissed before the read. To resolve this ambiguity with certainty
during live exploration (not for use inside a shipped test — Playwright's
auto-retrying `expect(locator).to_be_visible()`/`to_contain_text(...)`
called *immediately* after the triggering click is the correct in-test
mechanism, since its polling window catches a toast a single read would
miss), install a `MutationObserver` on `document.body` BEFORE triggering
the action:

```js
window.__toastCapture = [];
const observer = new MutationObserver(() => {
  const toast = document.querySelector('[data-testid="toast-message"]');
  if (toast) window.__toastCapture.push({ t: Date.now(), text: toast.textContent });
});
observer.observe(document.body, { childList: true, subtree: true });
window.__toastObserver = observer;
```

Then trigger the upload, and read `window.__toastCapture` afterward.
Confirmed live (ELITEA-1826): captured the toast's `textContent` on two
separate upload actions, byte-identical to the case's expected string both
times — this is what let the analyst assert `ready-for-automation` instead
of leaving a fidelity caveat, since the exact text was independently proven,
not just visually skimmed off a screenshot.

## `click_upload_path_upload_button_and_capture_response()` is single-response only

Added for ELITEA-1808 (`artifacts_page.py`, wraps `page.expect_response()`
around ONE matching PUT). It is only safe for uploads that fire exactly one
network request. Any case whose "Upload" click fires N>1 concurrent PUTs —
confirmed live for ELITEA-1826: uploading 3 new (non-duplicate) files fires
THREE separate `PUT .../artifacts/s3/{bucket}/{file}` requests from a single
click — must NOT use this helper; `expect_response()`'s first-match
semantics will only capture one of the N responses, non-deterministically.
For multi-file uploads, either register N separate `expect_response()`
matchers (one per filename) around the click, or — the project's established
preference, per ELITEA-1808's own documented rejection of
`capture_requests_matching()` for positive multi-request assertions (a
`status: None` pairing race) — skip network-response assertions entirely and
rely on condition-based file-table waits (`file_exists()` per name /
`get_total_file_count_from_pagination()`) as the completion signal.
