---
name: A testid on a MUI component lands on the wrapper, not the interactive node
description: Passing data-testid to a MUI TextField/Checkbox/Tooltip/Dialog puts it on the outer wrapper div/span, not the <input>/button the test needs to drive. Relocate it via inputProps/slotProps at the source — never chain .locator("input") off the wrapper, which is a raw handle and blocks review.
type: feedback
---

## Rule

MUI spreads unknown props onto its **root** element. So
`<TextField data-testid="x" />` renders `data-testid="x"` on the wrapper
`div`, and `page.get_by_test_id("x").fill(...)` fails or silently targets the
wrong node. The fix belongs in the JSX, at `add-data-testid` time — not in the
page object.

- **Relocate at the source.** `inputProps={{ 'data-testid': 'x' }}` (MUI v5) or
  `slotProps={{ htmlInput: { 'data-testid': 'x' } }}` (v6+) puts it on the real
  `<input>`. For `Checkbox`, the testid lands on the root `span`; the nested
  `<input type="checkbox">` is what carries checked state.
- **Never chain `.locator("input")` off the wrapper's descriptor.** That is a
  raw non-testid handle by the mechanical grep's definition and is
  `CHANGES_REQUESTED` — regardless of the fact that the parent is testid'd.
- **Verify after adding, before writing the locator:** live
  `document.querySelector('[data-testid="x"]').tagName` — `DIV`/`SPAN` means
  you are not done. Do this in the same HMR cycle; it costs one evaluate.
- **Known-good exceptions where the wrapper is genuinely the target:** MUI
  radio with the testid on the `label` still supports `is_checked()` (verified);
  a `Tooltip`'s static `aria-label` sits on the trigger wrapper by design and is
  the correct read for tooltip text.
- **Shared components:** wire a caller-supplied `testId` / `<part>TestId` prop
  rather than hardcoding — and remember the prop name convention is `testId`,
  never `dataTestId` (`.agents/testing.md` § Locator policy).

## Seen 5×

- `mui_form_field_quirks.md` — TextField wrapper vs input, the original observation.
- `basemodal_data_testid_lands_on_wrapper_and_upload_test_files_use_tmp_path.md` — BaseModal forwards to its wrapper.
- `discardbutton_confirm_testid_propname_mismatch_and_categoryfilter_wrapper_testid.md` — CategoryFilter wrapper testid + a prop-name mismatch on the confirm button.
- `upload_path_dialog_split_prefix_vs_input_and_backspace_workaround_false.md` — split prefix/input structure; the testid did not reach the editable node.
- `mui_tooltip_aria_label_wrapper_differs_from_click_target_testid.md` — tooltip wrapper vs the click target's own testid.

> Not covered by `.claude/rules/mui-patterns.md` (which explains
> `press_sequentially` and debounce, not testid placement) — which is why this
> earns an index line rather than living only in the per-surface notes.

See also: mui_form_field_quirks.md ·
basemodal_data_testid_lands_on_wrapper_and_upload_test_files_use_tmp_path.md ·
discardbutton_confirm_testid_propname_mismatch_and_categoryfilter_wrapper_testid.md ·
upload_path_dialog_split_prefix_vs_input_and_backspace_workaround_false.md ·
mui_tooltip_aria_label_wrapper_differs_from_click_target_testid.md ·
mui_radio_testid_on_label_is_checked_works.md ·
../qa-engineer/mui_checkbox_testid_lands_on_root_not_input.md
