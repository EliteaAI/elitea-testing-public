---
name: MUI form field quirks
description: Reusable Playwright/MUI gotchas found implementing ELITEA-1737 (skill export/import) — wrapper-testid resolution, replacing pre-filled text, download filenames, silent maxlength truncation
type: feedback
---

## MUI multiline TextField testid resolves to the wrapper, not the field

A `data-testid` set on an MUI `TextField`/custom input-enhancer component
lands on the `MuiFormControl-root` **wrapper `<div>`**, not the actual
`<input>`/`<textarea>`. Confirmed for skill name/description fields.
`.input_value()` / `.text_content()` calls need an explicit descendant
locator:

```python
self.description_input.locator("textarea").first.input_value()
self.name_input.locator("input").input_value()
```

Same pattern confirmed on the shared `DeleteEntityModal` TextField
(`delete-confirm-name-input`, used by skill/agent/pipeline delete-via-menu
dialogs): `Dialog.type_to_confirm()` in `components/mui.py` resolves it as
`dialog.get_by_test_id("delete-confirm-name-input").locator("input")`, with
a fallback to the pre-existing bare `dialog.locator("input")` for any
dialog that doesn't carry the testid yet — kept backward-compatible
because it's a shared helper with 3 merged callers.

Multiline fields render **two** `<textarea>` elements — the real editable
one plus an `aria-hidden="true" readonly tabindex="-1"` autosize shadow
copy used for height calculation. The real one is reliably `.first` in DOM
order, but verify live if a new field looks off (it can vary by MUI
version/config).

## Replacing content in an ALREADY-POPULATED MUI textarea

`click() + Control+a + keyboard.type()` (the project's standard
`_fill_text_input` pattern) reliably **fills an empty field**, but on a
field that already has text, `Control+a` does not reliably select the
existing value first — typed text ends up **inserted**, not
**replacing**, producing a doubled/garbled value
(`"new text" + "old text"`). Confirmed via manual `playwright-cli`
reproduction before committing the fix.

Working pattern for edit-in-place:

```python
field = self.description_input.locator("textarea").first
field.click()
field.select_text()          # Playwright Locator.select_text() — reliable full-select
page.wait_for_timeout(100)
page.keyboard.press("Backspace")
page.wait_for_timeout(100)
page.keyboard.type(new_text)
```

## `Download.path()` does not preserve the suggested filename/extension

Playwright stores downloads at an internal temp path with a random
basename — it does **not** keep the original extension. Any flow that
re-uploads the downloaded file and the app validates the extension
client-side (e.g. `file.name.endsWith('.md')`) will silently fail import
validation if you `set_files(download.path())` directly. Fix:

```python
download_path = Path(tempfile.gettempdir()) / download.suggested_filename
download.save_as(download_path)
# upload download_path, not download.path()
```

## Silent client-side maxlength truncation

Elitea skill name field has `MAX_NAME_LENGTH = 32` enforced via the input's
HTML `maxlength` attribute — no validation error shown, it just silently
truncates typed characters past the limit. A generated test name like
`f"elitea-1737-export-skill-{uuid_suffix}"` (34 chars) truncates to 32 and
then fails a downstream equality assertion in a way that looks like a
product defect but is test-data-length error. Keep generated kebab-case
names short (prefix + short suffix, verify total length <= the field's
known max) rather than assuming free-form length.

## MUI Autocomplete forwards unknown props to its root element

`AutoCompleteDropDown`/MUI `Autocomplete` spreads `{...props}` onto the
root component **last**, after its own explicit props (`id="options-filled"`
etc.) — so passing an extra prop like `data-testid="my-testid"` through a
wrapper component (e.g. `TagEditor`) does land in the DOM, on the
Autocomplete's root wrapper `<div>` (not the inner `<input>`). Confirmed
live via `playwright-cli` eval before wiring the locator. Useful pattern
when adding a testid to a third-party-style component that doesn't have an
explicit testid prop of its own — but always verify placement live, since
prop-spread order varies by component.
