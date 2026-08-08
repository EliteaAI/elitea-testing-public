---
name: Build with AI create-failure uses toast, not inline alert
description: GenerateEntityModal's create/approve failure surfaces via app-wide toast, unlike its own generation-failure path
type: reference
---

`GenerateEntityModal.jsx` (the shared "Build with AI" modal — Agent/Skill/etc.)
has TWO distinct failure paths that surface errors differently, within the
SAME component:

- **Generation failure** (`handleGenerate` catch, `GenerateEntityModal.jsx:79-82`):
  resets `step` to `STEPS.INPUT`; the input step then renders an inline MUI
  `Alert severity="error"` INSIDE the modal body
  (`generate-agent-error-alert` / `errorAlertTestId`, `role="alert"`) reading
  `generateError?.data?.error`. Covered by ELITEA-1915.
- **Create/Approve failure** (`handleApprove` catch, `GenerateEntityModal.jsx:98-101`):
  calls ONLY `setIsApproving(false)` + `toastError(buildErrorMessage(err))` —
  it does **NOT** render any inline alert, and does **NOT** call
  `handleClose()` (that's inside the `try` block, success-only). The error
  reaches the user via the APP-WIDE toast (`Toast.jsx`, testids `toast-alert`
  / `toast-message` / `toast-dismiss-button` — the same shared Snackbar+Alert
  component `AgentDetailPage`/`ChatPage`/`PipelineDetailPage`/etc. already use
  elsewhere), rendered as a sibling of `main`, OUTSIDE the modal's `dialog`
  subtree, top-center, and it auto-hides after a few seconds (assert
  immediately after the failed response resolves, don't wait then check).
  Covered by ELITEA-1916.

**Why this isn't classified as a defect**: cross-checked against the REGULAR
(non-AI) Create Agent form's own error handling (`useCreateApplication.jsx:85-107`)
— it shows field-level errors ONLY for array/`loc`-shaped validation errors
(via `formik.setFieldError`), and does literally nothing user-visible
(`console.error` only, no toast, no inline message) for a generic/scalar
error. There is no single "standard creation error handling" in this app to
hold Build-with-AI's create-failure path to — the toast is, if anything, a
stronger signal than the regular form's silent fallback for the same failure
class.

**If a future case's text says "form-level error" or similar for a
Build-with-AI CREATE (not generation) failure**: expect a toast, not an inline
alert, and don't file it as a defect on that basis alone — same reasoning as
ELITEA-1916's AFS Known Defects #1. Data survives the failure either way
(`draftData`/selected-resource state is untouched by the catch block), and the
same Approve button is genuinely re-enabled for retry (`isApproving` reset,
`isDraftValid` never touched).
