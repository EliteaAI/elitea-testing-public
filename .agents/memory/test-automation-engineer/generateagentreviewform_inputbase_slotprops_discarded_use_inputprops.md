---
name: Input.InputBase silently discards caller's slotProps — use inputProps
description: EliteaUI's shared Input.InputBase wrapper JSX-overrides any slotProps prop the caller passes with its own; only a top-level inputProps prop reaches slotProps.htmlInput on the underlying MuiTextField. A caller's slotProps={{htmlInput:{...}}} (incl. maxLength) is a silent no-op through this component.
type: feedback
---

## What happened (ELITEA-1920 fix round 2)

`GenerateAgentReviewForm.jsx`'s Name/Description/Instructions fields use the
shared `Input.InputBase` component (`src/[fsd]/shared/ui/input/InputBase.jsx`),
called like:

```jsx
<Input.InputBase
  ...
  slotProps={{ htmlInput: { maxLength: MAX_NAME_LENGTH } }}
  ...
/>
```

`InputBase.jsx` destructures a top-level `inputProps` prop (NOT `slotProps`),
so any `slotProps` the caller passes flows into its `...leftProps` rest and is
then spread onto the internal `<MuiTextField {...leftProps} ... slotProps={{
input: {...}, htmlInput: inputProps, inputLabel: {...} }} />`. Because the
explicit `slotProps={...}` JSX attribute is declared AFTER the `{...leftProps}`
spread on the same element, it **completely overrides** (shallow, whole-object)
whatever `leftProps.slotProps` held — including the caller's `htmlInput`. Since
the caller never passed a prop literally named `inputProps`, the internal
`htmlInput: inputProps` resolves to `htmlInput: undefined`.

**Net effect: `slotProps={{ htmlInput: {...} }}` passed to `Input.InputBase` is
a silent no-op** (this pre-existed my change — `MAX_NAME_LENGTH`'s native
`maxLength` was already not enforced on the input before I touched the file;
not something I fixed, flagged as a note only, out of this fix round's scope).

**To actually reach the native `<input>` through `Input.InputBase`, pass a
top-level `inputProps` prop** (not `slotProps`):

```jsx
<Input.InputBase
  ...
  slotProps={{ htmlInput: { maxLength: MAX_NAME_LENGTH } }}  {/* pre-existing, still dead */}
  inputProps={{ 'data-testid': 'generate-agent-review-name-input' }}  {/* this reaches the input */}
  ...
/>
```

Verified live: the testid rendered correctly on the `<input>` (not a wrapper)
and `expect(locator).to_have_value(...)` resolved against it in 3/3 green runs.

## Relation to the general rule

This is a **different mechanism** than the general "MUI spreads unknown props
onto the wrapper" rule (see the indexed `testid_lands_on_mui_wrapper_not_input.md`
— that's about plain `MuiTextField`/`Checkbox`/etc. receiving an unrecognized
prop). Here the wrapper is a **custom EliteaUI component** with its own prop
name (`inputProps`) that happens to differ from what the caller already had in
scope (`slotProps`) for an unrelated purpose (maxLength). Same failure mode
(testid attribute never reaches the html input) via a different root cause
(prop-name mismatch + full-object override in a custom wrapper, not MUI's
generic root-prop-spreading) — worth checking BOTH before assuming a testid
addition to any `Input.InputBase`-based field actually worked. Verify with a
live DOM check (`document.querySelector('[data-testid="x"]').tagName === 'INPUT'`)
before writing the page-object locator, same discipline as the general rule.

## Scope

Only `Input.InputBase` (`src/[fsd]/shared/ui/input/InputBase.jsx`) has this
specific `inputProps`-vs-`slotProps` split — other MUI-direct usages (e.g. the
Skill review form's plain `<TextField slotProps={{ htmlInput: {...} }} />`)
work exactly as expected, since there's no custom wrapper discarding the prop.
Check which component a field uses before assuming the fix pattern transfers.
