---
name: StyledInputEnhancer/InputBase data-testid needs inputProps, not a bare prop
description: A bare data-testid passed to Input.StyledInputEnhancer/InputBase lands on MuiTextField's outer wrapper div, not the actual <input>/<textarea> — must go through inputProps={{ 'data-testid': ... }} (-> slotProps.htmlInput) to land on the editable node.
type: feedback
---

EliteaUI's `Input.StyledInputEnhancer` (`src/[fsd]/shared/ui/input/StyledInputEnhancer.jsx`)
wraps `Input.InputBase`, which renders an MUI `<TextField>` and spreads any
unrecognised prop (`{...leftProps}`) directly onto that `TextField` — MUI
TextField forwards unknown/rest props to its **root wrapper**, not the inner
native `<input>`/`<textarea>`. So threading a bare `data-testid` prop through
`StyledInputEnhancer` (the way `BaseModal`'s `data-testid`/`titleTestId`/
`confirmButtonTestId` work) lands the testid on a `<div>` — Playwright can
find it via `get_by_test_id`, but `.fill()`/`.type()` on that locator fails
(not an editable element).

**Fix:** pass it via `inputProps={{ 'data-testid': someTestId }}` instead —
`InputBase` explicitly threads its `inputProps` prop to
`slotProps.htmlInput` on the underlying MUI `TextField`, which MUI applies
directly to the native `<input>`/`<textarea>` DOM node. Confirmed live
(ELITEA-2304, `InviteUserDialog`'s emails textarea): `inputProps={{
'data-testid': emailsInputTestId }}` → `document.querySelector('[data-testid=...]').tagName
=== 'TEXTAREA'`.

Before adding a testid prop to any `StyledInputEnhancer`/`InputBase`
consumer, check whether it exposes a caller-facing prop that forwards into
`inputProps` (most do, since `InputBase` always threads it to
`slotProps.htmlInput`) — thread the testid through THAT path, not as a bare
`data-testid`. Distinct from (but complements) the existing
`basemodal_data_testid_lands_on_wrapper_and_upload_test_files_use_tmp_path.md`
entry, which covers `BaseModal`'s own testid-forwarding quirks and the
dead-`cancelButtonTestId`-with-custom-`actions` pattern — that pattern
applies here too (both `InviteUserDialog` and `EditUserRolesDialog` pass a
custom `actions` node, so their Save/Invite buttons need `data-testid`
directly on the caller's own `Button.BaseBtn`, not via BaseModal's
`confirmButtonTestId`).
