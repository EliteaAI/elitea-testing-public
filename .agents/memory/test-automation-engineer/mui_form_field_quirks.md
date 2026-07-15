---
name: MUI form field quirks
description: Reusable Playwright/MUI gotchas found implementing ELITEA-1737/1738/1790 — wrapper-testid resolution, replacing pre-filled text, download filenames, silent maxlength truncation, SingleSelect option testids, Tooltip-on-disabled-child label placement
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

## Shared `SingleSelect` component: per-option testid is keyed to `value`, not `label`

`SingleSelectMenuItem.jsx` already carries a generic
`data-testid={`select-option-${option.value}`}` on every MUI `Select`
dropdown item app-wide (from an earlier EL-5010 pass). Fine when
`option.value` happens to equal a stable, known-ahead-of-time string (e.g.
the voice picker in `user_profile_settings_page.py`, where
`value === name.lower()`). **Not usable when `value` is a numeric/opaque id
the test doesn't know until runtime** (e.g. a version's DB id, only known
after creating it) — confirmed for `SkillTabBar`'s VERSION selector
(`buildVersionOption()` sets `value: id`).

Fix (ELITEA-1738 rework): added an *optional* `option.testId` field.
`SingleSelectMenuItem` now does
`data-testid={option.testId ?? `select-option-${option.value}`}` —
additive, zero regression risk for existing callers that never set
`option.testId`. `buildVersionOption()` (`version.helpers.jsx`) sets
`testId: `version-option-${name}`` so every version-selector consumer
(skill/agent/pipeline) gets a name-keyed option testid for free. Also had
to add `data-testid` pass-through to `SingleSelect.jsx` itself (it
destructures every prop explicitly, no `...rest` spread, so a new prop
needs an explicit destructure + forward — unlike `BaseBtn`/`BaseModal`
which already had `data-testid`/`*DataTestId` plumbing).

**Pattern for any future "generic component's existing testid is keyed to
the wrong field" situation**: don't rip out the existing testid (blast
radius = every consumer); add an optional override field on the data object
the component already renders from, with the old testid as the fallback.

## MUI `Tooltip` wraps disabled children: the accessible label lands on the wrapper span, not the child

When a `<Tooltip title="...">` wraps a `<Box component="span">` that in turn
wraps a `disabled` button (`SkillMenu.jsx`'s "+ Skill" add button at the
5-skill limit), MUI moves the tooltip's accessible label/description to the
wrapper `<span>`, never onto the disabled child — disabled elements don't
fire hover/focus events, so MUI can't attach the tooltip mechanism there.
Confirmed live (ELITEA-1790 rework): `<Box component="span" aria-label="...">`
wraps `<BaseBtn disabled ... data-testid="agent-add-skill-button">`.

A testid on the inner button does NOT let you read the tooltip text off
that same element — `.get_attribute("aria-label")` on the button returns
`None`. Two compliant options, in order of preference:
1. If the wrapper is plain first-party JSX (usually is, for a `Box`/`span`
   wrapper an app author wrote), give **it** its own testid too
   (`{section}-{element}-tooltip`) via `add-data-testid` — this project's
   testid-only policy forbids reaching the wrapper via a raw
   `xpath=".."`/`locator("..")` parent traversal chained off the button's
   field, even though it's tempting since the button field already exists
   (only `[data-testid="…"]` string/template constants are sanctioned scoped
   sub-selectors — see `.agents/testing.md` § Locator policy).
2. Only if the wrapper is a genuinely third-party/library-internal node you
   can't attach a prop to, stop+flag to the lead instead of improvising a
   raw selector.

Watch for this same shape (Tooltip + disabled child) anywhere else a
button/control becomes conditionally disabled with an accompanying tooltip
message — the label will be on the ancestor, not the control, and needs its
own handle.
