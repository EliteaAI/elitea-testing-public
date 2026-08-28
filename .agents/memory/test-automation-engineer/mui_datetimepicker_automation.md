---
name: MUI DateTimePicker automation on Elitea
description: How to drive an @mui/x-date-pickers v7 DateTimePicker with testid-only policy — what can carry a testid, what cannot, and the two traps that produce false reds
type: feedback
aliases: [date picker, DateTimePicker, calendar popper, picker day cell, Apply button]
tags: [area/ui-automation, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## What CAN carry an app testid

- The field `<input>` — `slotProps.textField.inputProps['data-testid']` (v7 renders a plain
  editable input, so `input_value()` works).
- The calendar icon — `slotProps.openPickerButton['data-testid']`.
- The popper root — `slotProps.popper['data-testid']`. This is the scoping parent that makes
  everything else legal under the #579 exception.

## What CANNOT (without a functional change)

Day cells (`PickersDay`), the month header/nav arrows (`PickersCalendarHeader`), and the
Clear/Apply buttons (`PickersActionBar`) accept no per-element testid — `slotProps.actionBar`
reaches only the container. Overriding the slot components would be a zero-functional-impact
violation. Use scoped raw handles inside the popper testid, declared in the method docstring.

## Two traps that cost a red each

1. **The outgoing month grid stays mounted during the slide transition**, so straight after a
   "Previous month" click the same day number resolves to 2-4 nodes (strict-mode violation).
   Wait for `expect(cell).to_have_count(1)` — a condition wait, not a sleep.
2. **Selecting a day fires the data request immediately (`onChange`); "Apply" fires nothing** and
   only closes the popper. Put the `expect_response` around the DAY CLICK. On Elitea the confirm
   button is labelled **"Apply"** (`localeText.okButtonLabel`), not "Ok" as TMS case texts say.

Constraint props (`maxDateTime`/`minDateTime`) are enforced by DISABLING out-of-range day cells and
the month-nav arrow — there is no error message, so "the picker prevents it" is asserted as
`is_disabled()` plus an unchanged value plus a negative network window.

Related: [[vite_dev_server_serves_stale_modules]]
