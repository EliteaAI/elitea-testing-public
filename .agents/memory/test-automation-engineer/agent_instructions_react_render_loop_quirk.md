---
name: Agent Instructions field React render-loop defect + deferred-assert pattern
description: Typing into any StyledInputEnhancer/InputBase MUI field (Name/Description/Instructions/Welcome) can trigger "Maximum update depth exceeded" (filed #538) — root cause is useAutoBlur()'s 10ms timer, not a per-field effect; and the pytest deferred-assert pattern for it
type: feedback
---

## The defect (elitea-testing-public#538) — REVISED root cause (ELITEA-2614, 2026-08-12)

Typing into `agent-instructions-input` (via `AgentFormPage.update_text_field()`'s
click + `ControlOrMeta+a` + `type()` sequence) can reliably trigger a React
console warning:

```
Warning: Maximum update depth exceeded. This can happen when a component
calls setState inside useEffect, but useEffect either doesn't have a
dependency array, or one of the dependencies changes on every render.
```

Stack trace runs through `InputBase2`/`FormControl2`/`TextField2`.

**Original suspected cause (below) was too narrow — it's NOT Instructions-
specific.** Root-caused live during ELITEA-2614: ALL of Name/Description/
Instructions/Welcome message share the `StyledInputEnhancer`/`InputBase`
wrapper (`src/[fsd]/shared/ui/input/InputBase.jsx`), which defaults
`enableAutoBlur=true` and drives it via `useAutoBlur()`
(`src/hooks/useAutoBlur.jsx`) — a hook that **restarts a 10ms timer on every
keystroke**, and when the timer actually fires (no keystroke came in for
10ms) it does `document.activeElement.blur(); document.activeElement.focus()`
on the field. Two consequences, both confirmed live:
- **Type with ANY per-keystroke delay ≥ ~10ms** (e.g. `press_sequentially(...,
  delay=20)`, matching `fill_form()`'s own delay) → the timer fires BETWEEN
  every keystroke → reliable "Maximum update depth exceeded" (2/2 runs,
  `test_import_agent_recreates_skills_with_new_ids.py`'s console-error
  assertion on the DESCRIPTION field, not Instructions).
- **Type instantly (no delay, the pre-existing `field.type(value)` default)**
  → the timer only fires once real typing pauses/ends → usually safe, but on
  a slow event-loop tick can still fire mid-typing → a DIFFERENT symptom: a
  corrupted final value (part of the OLD text's tail duplicated back in),
  not the console warning. Observed 1 of 3 local runs on the Description
  field (ELITEA-2614 Step 23).

So this is ONE shared timing race with TWO possible symptoms (console loop
warning vs. silent value corruption) depending on typing speed and luck, not
two separate per-field effects. `AgentFormPage.update_text_field()` (fixed
2026-08-12) types instantly AND verifies+retries once on a value mismatch —
this closes the corruption symptom but does NOT eliminate the timer itself,
so the console warning can still appear on an unlucky run. Any NEW page-object
method that types into one of these fields should do the same (instant type +
read-back verify), and should NOT copy `fill_form()`'s `delay=20` pattern for
an EDIT/update path — that pattern is fine for the CREATE form's initial fill
into empty fields (shorter strings, less exposure) but is the WRONG default
to reach for on a longer replace-the-whole-value edit.

**Isolation, confirmed via a throwaway probe test** (create dedicated agent →
navigate only → capture console; then navigate → type only → capture console;
then → save only → capture console):
- Does NOT fire on plain page navigation/load.
- DOES fire reliably during the typing/onChange sequence (more reliably the
  slower/more evenly-paced the typing).
- Does NOT block the Save PUT (still 201) or persistence after reload —
  when it manifests as the console warning, it's console-warning-only, not
  functionally blocking; when it manifests as value corruption, the corrupt
  value IS what gets saved (a real functional consequence, needs the
  verify+retry).

If a future case's manual/analyst run reports "zero console warnings" but the
automated run reproduces this — it's not a masking bug in the analyst's pass,
it's a real, timing/speed-sensitive React loop that manual clicking might not
trigger as reliably as scripted `type()`/`press_sequentially()` input. Don't
assume the analyst missed it; the isolation probe (three separate scoped
console captures: navigate-only / type-only / save-only) is the fast way to
confirm before filing.

## The deferred-assertion pattern for isolated known defects (pytest, no `expect.soft()` target)

This project's existing known-defect precedent
(`test_credential_required_fields_validation.py`, #526) uses
`expect.soft()` when the defect is on a **Locator** target. But a
console-message list isn't a Locator — there's no `expect.soft()` equivalent
for a plain Python list assertion. The working pattern used here instead:

1. Keep capturing console messages across the whole flow (attach the listener
   before Step 1, same as always).
2. Do **not** assert on the list right after the action that triggers the
   defect (that would abort the test before the actual feature-under-test
   assertions run).
3. Move the `assert not console_messages` to its own final
   `allure.step("Side-channel check — ...")`, **after** every functional/
   persistence assertion in the case has already run and passed.
4. Reference the filed ticket in both the in-code comment at the triggering
   step and the assertion failure message.

Result: the test is stably RED at exactly one place (the final side-channel
check) while every real case assertion (Steps 1-5, the actual persistence
proof) demonstrably passes first — visible in the traceback (failure line
number is the last assert in the function) and in Allure (all case steps
green, only the side-channel step red). This is the pytest-native answer to
"soft assert a known defect without masking the rest of the test," matching
the spirit of `expect.soft()` for non-Locator assertions.

(from ELITEA-1872)
