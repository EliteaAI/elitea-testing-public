---
name: DiscardButton confirm-button testid prop-name mismatch + CategoryFilter wrapper-testid trap
description: Two EliteaUI shared-component testid bugs found and fixed during ELITEA-1868 implementer Phase 2/4 — DiscardButton.jsx forwarded confirmButtonDataTestId to Modal.BaseModal under the wrong prop name (BaseModal reads confirmButtonTestId), so the Warning-dialog confirm button never got a testid for ANY caller; and CategoryFilter.jsx's search TextField had data-testid on the MUI root wrapper, not the actual <input>, breaking to_have_value()/input_value() reads
type: feedback
---

## DiscardButton.jsx → BaseModal prop-name mismatch (real, pre-existing product bug)

`src/[fsd]/shared/ui/button/DiscardButton.jsx` accepts `dataTestId` /
`modalDataTestId` / `confirmButtonDataTestId` props and forwards them to
`Modal.BaseModal`. The first two forward correctly (`data-testid={dataTestId}`
on the trigger button, `data-testid={modalDataTestId}` on the dialog root) —
but the third forwarded as `confirmButtonDataTestId={confirmButtonDataTestId}`,
while `BaseModal.jsx` destructures `confirmButtonTestId` (no "Data" in the
name) and applies it as `data-testid={confirmButtonTestId}` on the dialog's
own confirm button. **The names don't match**, so the confirm-button testid
was silently a dead prop for every existing caller
(`CredentialsTabBar.jsx`'s `credential-discard-confirm-button`,
`ToolkitsTabBar.jsx`, etc.) — confirmed live by reading BOTH files, then
empirically: reverted `DiscardButton.jsx` to the buggy state via
`git checkout <parent-sha> -- DiscardButton.jsx`, drove the Credentials
detail page's Discard flow live, and confirmed
`credential-discard-confirm-button` was ABSENT from the DOM
(`credential-discard-confirm-modal` WAS present — only the confirm button's
testid was broken). Fixed by renaming the forwarded prop to
`confirmButtonTestId={confirmButtonDataTestId}` — `DiscardButton`'s own
public prop name (`confirmButtonDataTestId`) is unchanged, only its internal
wiring to `BaseModal` is corrected. Verified the fix doesn't regress: the
ALREADY-MERGED `test_credential_discard_changes.py` (which calls
`confirm_discard()` → clicks `discard_confirm_button`, testid
`credential-discard-confirm-button`) now passes cleanly — before the fix
that click would have targeted a testid that never rendered (a Playwright
`.click()` on zero matching elements times out, it doesn't silently no-op),
so this test was almost certainly latently broken and the fix is a genuine
repair, not a risk.

**Lesson: when wiring an "already-accepted unwired prop" per an AFS's testid
gap list, verify empirically that the prop actually reaches the DOM** — don't
assume a prop that exists in the component's destructuring is correctly
forwarded to whatever it's being passed to next. A prop can be consumed
(not leak into `...rest`) and still go nowhere if the downstream component
expects a different name. Confirmed live with `playwright-cli` /
`document.querySelectorAll('[data-testid]')` before trusting the wiring in a
test.

## CategoryFilter.jsx — MUI TextField testid lands on the wrapper, not the input

Passing `data-testid={x}` directly as a prop to MUI's `<TextField>` places
the attribute on the root `MuiFormControl-root` `<div>`, not the nested
native `<input>` — confirmed live: `tagName` was `DIV`, and Playwright's
`expect(locator).to_have_value(...)` failed with `"Not an input element"`.
Same class of bug as `artifacts_page.py`'s already-documented
`upload_path_input` (wrapper) vs `upload_path_input_field` (real input,
added via `slotProps.htmlInput`) — this is evidently a RECURRING MUI
`TextField` trap in this codebase, not a one-off. Fixed the same way:

```jsx
<TextField
  ...
  slotProps={{
    htmlInput: { 'data-testid': searchInputTestId },
  }}
/>
```

Confirmed live afterward: `tagName === "INPUT"`, `.value` reflects typed
text, `to_have_value()` passes. Other precedent in this codebase for the
same fix: `GenerateSkillReviewForm.jsx`, `UserInput.jsx`
(`chat-message-input`), `BlockWithCommentControl.jsx`.

**Rule of thumb for any NEW testid added to a bare `<TextField>` (not
`inputProps`/pre-`slotProps` legacy code) in this codebase: always verify
`.input_value()`/`to_have_value()` works before shipping — a testid that
merely renders (visible in a DOM snapshot) is not proof it's on the actual
editable element.** A quick live check
(`playwright-cli --raw eval "el => el.tagName" "getByTestId('...')"`) catches
it in one line.

## Shared-component testid scoping — searchInputTestId

`CategoryFilter`/`GroupedCategory` (`src/[fsd]/shared/ui/filter/` +
`src/[fsd]/shared/ui/category/`) are shared by BOTH
`ToolkitTypeSelector.jsx` (Toolkit/MCP/Application creation, via
`isMCP`/`isApplication` props) AND `CredentialTypeSelector.jsx`. Added an
optional `searchInputTestId` prop threaded through both layers, but only
wired it at `ToolkitTypeSelector.jsx`'s call site, conditionally
(`!isApplication && !isMCP`) so `toolkit-wizard-type-search-input` never
renders on the MCP/Application creation paths this case doesn't touch — per
the project's "testid scope is load-bearing" ruling
(`.agents/testing.md`/`.agents/role-overrides.md`: testids go only on
elements a test actually touches). `CredentialTypeSelector.jsx` gets no
testid at all from this change (untouched call site).
