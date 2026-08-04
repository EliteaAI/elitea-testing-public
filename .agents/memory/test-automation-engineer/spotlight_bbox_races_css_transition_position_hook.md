---
name: Spotlight bounding-box read races the CSS-transition position hook
description: interactive-tour-spotlight (and any element positioned by an async measurement hook + CSS transition) needs a condition-wait on the bbox itself, not a read right after the step-counter/title assert resolves.
type: feedback
---

## What happened (2026-08-05, ELITEA-2227)

`InteractiveTourSpotlight` is positioned via `useTourCardPosition`, which
measures the target element and feeds `top`/`left`/`width`/`height` into a
`Box` with a `0.35s` CSS `transition`. The tour dialog's title/counter React
state updates synchronously on `click_next()`, so `expect(step_counter).to_have_text(...)`
resolves immediately — but the spotlight's *position* hook can still be
mid-transition (or not yet re-measured) at that instant. Reading
`.bounding_box()` right after the counter/title assertion intermittently
returned the SAME rect as the previous step (raced the position update), one
test run in five.

## The fix

Added `InteractiveTourCard.wait_for_spotlight_change(previous_bbox, timeout)`
— a `page.wait_for_function()` condition wait that polls
`getBoundingClientRect()` on the spotlight testid until it differs from
`previous_bbox`, then returns the new box. This is rule #3 of
`never_assume_a_transition_settled.md` in a new shape: "the element that
proves the transition landed is not the element whose state you just
asserted" — title/counter settle on one clock (React re-render), the
spotlight rect settles on another (async measure + CSS transition). Never
assume reading state A tells you state B has also settled.

## Pattern to reuse

Any Playwright test asserting a *derived, animated* value (bounding box,
computed style, scroll position) driven by a *different* state signal than
the one you just waited on needs its own condition wait — `wait_for_function`
polling the DOM, not a sleep, and not "the other assert already resolved so
this one's safe too."
