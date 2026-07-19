---
name: Upload-path dialog split prefix/input, and the Backspace-clears-defect workaround is false
description: UploadPathDialog.jsx's Path field's testid resolves to the wrapper — text_content() never includes what the user typed; a documented "select_text()+Backspace clears the buggy prefix" workaround was verified live to do nothing (the buggy value lives in a read-only sibling div, not the editable input) — the real fix is close-dialog + re-navigate-to-root + retry
type: feedback
---

## The field split (ArtifactsPage / UploadPathDialog.jsx)

`artifacts-upload-path-input` (the existing testid, on the MUI `TextField`)
resolves to the `MuiFormControl-root` **wrapper** — label ("Path") + the
read-only `InputAdornment` (`{bucket}/{currentPrefix}`), rendered via
`slotProps.input.startAdornment`. A native `<input>`'s **value is never
part of any ancestor's `text_content()`** — this is standard DOM behavior,
not a framework quirk, but it's easy to miss when a prior analyst pass
*claims* (without re-verifying after typing) that `text_content()` reflects
"the combined path". Verified live: typing `"a1"` into the field, then
re-reading `text_content()`, returned the exact same unchanged string —
`'Path​autotest-.../​'` — with zero trace of the typed value.

**Fix**: added a genuinely new testid, `artifacts-upload-path-input-field`,
on the actual `<input>` via `slotProps.htmlInput` — the SAME established
pattern already used elsewhere in this codebase (`grep -rn "htmlInput"
src/` finds `UserInput.jsx:440`, `CreateSkillForm.jsx:184` with nearly
identical comments) — don't invent a new mechanism, this one's precedented.
New `ArtifactsPage` methods: `get_upload_path_normalized_prefix()` (strips
the "Path" label + `​` padding from the wrapper's `text_content()`),
`get_upload_path_typed_value()` (`.input_value()` on the new field testid),
`get_upload_path_combined_text()` (concatenates both — this is what a case
step describing "the combined Path text" actually needs).

**Interaction gotcha, not just reading**: `.click()`+`.type()` on the OUTER
wrapper DOES land correctly on the inner input for a SHORT bucket name (own
diagnostic confirmed this), but with a LONG bucket name (a long test
function name → a long generated bucket name) the read-only prefix can
occupy most of the field's width, and a center-click on the wrapper can
miss the actual `<input>` entirely — 10s of `expect(...).to_have_value()`
timeout with the value staying `""`. Click+type on the dedicated
`upload_path_input_field` testid directly, not the wrapper, once that
testid exists.

**Race, not a defect**: reading `.input_value()` immediately after `.type()`
can still catch it empty — Playwright's `.type()` returns once keyboard
events are dispatched, not once React's controlled-input re-render has
settled. Fix is `expect(locator).to_have_value(expected, timeout=...)`
before reading — itself a legitimate strengthening assertion, not a
workaround-for-a-workaround.

## The false "Backspace clears the buggy prefix" workaround (defect #649)

Known defect #649: the bucket-menu "Upload files" entry point pre-fills the
dialog's Path with `{bucket}/{currentPrefix}` (inherited from wherever the
user is currently navigated), instead of resetting to bucket root. An
earlier AFS pass claimed the workaround was `select_text()` + Backspace on
`artifacts-upload-path-input` to "clear the Path field back to empty."
**Verified live this is false**: 10 consecutive Backspace presses on the
focused (empty) input produce **zero change** to the adornment text, and
the resulting upload PUT still lands at the buggy (non-root) location. Root
cause, confirmed via `UploadPathDialog.jsx` source: the buggy prefix lives
in a **read-only sibling `<div>`** (the `InputAdornment`, driven directly
by the `currentPrefix` prop) — a focused `<input>`'s Backspace keystroke
cannot edit a sibling DOM node; there is no in-dialog control that resets
`currentPrefix`.

**Verified-working replacement**: (1) close the dialog via `Escape` — no
new testid needed; confirmed `BaseModal`'s `onClose` (the same handler the
untestid'd "Cancel" button calls) fires on Escape — (2) click the bucket's
own row to navigate back to root (`currentPrefix` becomes `""`), (3)
re-open the SAME upload flow a second time — now correctly pre-filled at
root (confirmed live 1/1, then stable across 3 full clean-process test
runs). New `ArtifactsPage.close_upload_path_dialog()` method for step (1).
This changes WHICH interactions reach the case's required end state
(sample.md at bucket root via the bucket-menu entry point) but not WHAT is
asserted — stayed within implementer Phase-2 technique latitude, amended
into the AFS in the same PR rather than `needs-analyst-rerun`.

**General lesson**: when an AFS claims a specific interaction technique
"confirmed live," and your own Phase 2 pass needs that exact technique,
re-verify it with a real DOM dump (outerHTML, not just a text assertion)
before trusting it — this is the second time in this project's history a
"confirmed live" technique claim didn't hold up under fresh re-verification
(see also `analyst_absence_claims_need_normal_viewport_reverification.md`).
Both times the fix was cheap once the actual DOM structure was inspected
directly rather than inferred from the claim's prose.

(from ELITEA-1824, PR #653)
