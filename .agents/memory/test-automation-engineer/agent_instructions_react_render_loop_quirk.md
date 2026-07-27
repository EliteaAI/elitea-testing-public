---
name: Agent Instructions field React render-loop defect + deferred-assert pattern
description: InstructionsInput.jsx typing triggers a real "Maximum update depth exceeded" console warning (filed #538) — isolated to typing, non-blocking; and the pytest pattern for deferring a known-defect console check so it doesn't mask the feature-under-test proof
type: feedback
---

## The defect (elitea-testing-public#538)

Typing into `agent-instructions-input` (via `AgentFormPage.update_text_field()`'s
click + `ControlOrMeta+a` + `type()` sequence) reliably triggers a React
console warning:

```
Warning: Maximum update depth exceeded. This can happen when a component
calls setState inside useEffect, but useEffect either doesn't have a
dependency array, or one of the dependencies changes on every render.
```

Stack trace runs through `InputBase2`/`FormControl2`/`TextField2` in the
Instructions field's MUI TextField stack (`InstructionsInput.jsx`). Suspected
cause: a `useEffect` in the variable-detection logic (scans typed text for
`{{variable}}` tokens, same feature area as ELITEA-1884) calls `setState` on
every keystroke without a stable dependency array.

**Isolation, confirmed via a throwaway probe test** (create dedicated agent →
navigate only → capture console; then navigate → type only → capture console;
then → save only → capture console):
- Does NOT fire on plain page navigation/load.
- DOES fire reliably during the typing/onChange sequence.
- Does NOT block the Save PUT (still 201) or persistence after reload —
  console-warning-only, not a functional defect.

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
