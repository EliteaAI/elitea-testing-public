---
name: Client-side-only React input interactions — replace fixed sleeps with a real condition, even with zero network requests
description: A page-object method whose interaction fires no network request (client-side only formik/React state update) still has a real completion signal to wait on instead of a guessed wait_for_timeout() duration — pick expect(locator).to_have_value(...) when the final value is deterministic, or a double requestAnimationFrame when it isn't (e.g. depends on clamp math the method itself shouldn't assert).
type: feedback
---

## The situation

GAP-003's `AgentFormPage.clear_step_limit()` and `paste_step_limit()` both
mutate a React-controlled input with **zero network requests** (confirmed
live — pure `formik.setFieldValue`, no PUT/POST fires). The first-pass
implementation used flat `page.wait_for_timeout(200)` / `(300)` sleeps
"because there's nothing to wait on." A reviewer flagged both as violating
`.agents/conventions.md`'s "No sleep/waitForTimeout — framework waits only"
rule — correctly: *zero network requests* doesn't mean *zero completion
signal*, it just means the signal isn't `wait_for_response`.

## The fix — two different conditions depending on what you can know

**When the method's own contract determines the final value** (e.g.
`clear_step_limit()` — the entire point of "select-all + Delete" is that the
field becomes `""`, always, per `isValidStepLimit('')`):

```python
self.step_limit_input.press("ControlOrMeta+a")
self.step_limit_input.press("Delete")
expect(self.step_limit_input).to_have_value("", timeout=2000)
```

This is the exact pattern already established elsewhere in this codebase
(`mcp_form_page.py:477`, `expect(locator).to_have_value("", timeout=...)`)
— reviewers will recognize it immediately.

**When the final value depends on logic the page object shouldn't
re-implement** (e.g. `paste_step_limit()` — whether `"1500"` clamps to
`"999"` is the CLAMP MATH, which belongs to the test's assertion, not the
page object's wait condition — asserting a specific post-value inside the
page object would either hardcode business logic into the abstraction layer
or silently mask a real clamp-logic regression as a timeout instead of a
clear failed assertion):

```python
self.step_limit_input.evaluate(
    """(el, value) => {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(el, value);
        el.dispatchEvent(new Event('input', { bubbles: true }));
    }""",
    value,
)
# double rAF: guarantees the browser has completed a paint cycle since the
# synthetic input event fired — by which point React's synchronous
# onChange -> setState -> commit has definitely flushed to the DOM.
self.page.evaluate(
    "() => new Promise(resolve => "
    "requestAnimationFrame(() => requestAnimationFrame(resolve)))"
)
```

Why double, not single, rAF: a single `requestAnimationFrame` fires at the
START of the next frame, before that frame's layout/paint completes for
updates scheduled DURING the current callback; waiting for a second rAF
guarantees the update scheduled by the dispatched event has actually been
painted, not just queued. This is the standard "wait for React to finish
rendering" idiom used in Playwright/Cypress test suites generally — not
project-specific — worth reaching for whenever a synthetic DOM event is
dispatched and the caller needs the resulting re-render's OUTPUT to be
readable afterward, but doesn't want to bake a specific expected value into
the page-object method itself.

## The distinguishing question

Before reaching for a sleep on ANY client-side interaction, ask: **"is there
exactly one correct outcome regardless of any bug, or does the outcome
depend on logic I don't want to duplicate here?"** — the first case gets a
value-based `expect()`; the second gets a render-completion wait
(`requestAnimationFrame` chain) that stays agnostic to what the DOM ends up
showing, leaving the actual correctness assertion where it belongs: the
test, not the page object.
