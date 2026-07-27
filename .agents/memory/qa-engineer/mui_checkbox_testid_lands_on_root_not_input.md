---
name: MUI Checkbox testid lands on root span, not the nested input
description: PR #644/ELITEA-1840 reviewer-verified from MUI source — any data-testid threaded onto an MUI Checkbox (via BaseCheckbox's ...restProps or a direct prop) resolves to the outer ButtonBase/SwitchBase root, never the <input>; Playwright's is_checked() will raise on that locator, read the Mui-checked class instead
type: feedback
---

Confirmed by reading `@mui/material`'s own source in `EliteaUI/node_modules`
during PR #644/ELITEA-1840's review (not just trusting the implementer's
explanation):

- `Checkbox.js` destructures `{ ...other }` (everything not an explicit
  Checkbox prop, including any `data-testid`) and spreads it onto `RootSlot`
  (`CheckboxRoot = styled(SwitchBase)`) — **never** onto `slotProps.input`.
- `SwitchBase.js`'s `useUtilityClasses` composes the `checked` slot for the
  SAME root element. `checked` is one of `@mui/utils/generateUtilityClass`'s
  fixed `globalStateClasses` (`active`, `checked`, `disabled`, `error`,
  `selected`, …), which always resolve with the `Mui-` prefix regardless of
  component name — so it's literally the class string `Mui-checked`, not a
  per-component-namespaced class.
- Net effect: **any testid attached to an MUI `Checkbox` (directly, or via a
  wrapper like this project's `BaseCheckbox` that forwards `...restProps`)
  lands on the same outer `<span class="MuiButtonBase-root MuiCheckbox-root
  ...">` element that also carries `Mui-checked` when checked — never on the
  nested `<input type="checkbox">`.**

Consequences for any future EliteaUI test touching an MUI checkbox in this
codebase:
- `Locator.click()` on the testid works fine (`ButtonBase` handles the click
  and toggles the underlying input).
- Playwright's `Locator.is_checked()` will raise `"Not a checkbox or radio
  button"` when pointed at that testid — the element itself isn't the
  input/`role=checkbox` semantically enough for Playwright's own state check.
- The correct read is `checkbox.get_attribute("class")` and test for
  `"Mui-checked" in class_attr` — this reads an *attribute of the
  already-testid-anchored locator* (same technique as reading a progress
  bar's `aria-valuenow`), not a new chained/raw selector, so it stays
  testid-only-policy compliant. See
  `automation/pages/artifacts_page.py::ArtifactsPage.is_file_checkbox_checked()`
  for the reference implementation.

This is a durable MUI-library fact, not project-specific — it will recur on
any future case (Secrets/Tokens/Users/BucketAccess/DataTable/
NotificationTable tables, or any other MUI `Checkbox`/`Radio` usage) that
needs to read a checked/selected state rather than just click it.
