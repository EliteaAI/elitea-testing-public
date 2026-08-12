---
name: press_sequentially can drop the leading keystroke on a plain search input
description: On a simple native-<input>-backed search box (no MUI TextField/masking layer), press_sequentially() dropped the first character in a full test-flow run (not in an isolated minimal script) — .fill() is this codebase's proven pattern for exactly that shape and doesn't have the issue.
type: feedback
---

## What happened

`AnalyticsUsers.jsx`'s search-by-email input is `SearchInput.jsx` — a plain
MUI `<Input>` wired straight to `onChange`, no masking/formatting layer. Using
`click()` + `press_sequentially("testbot", delay=50)` (the mui-patterns.md
default for MUI form fields) reliably typed `"testbot"` in an isolated
minimal reproduction script, but **dropped the leading "t"** (typed
`"estbot"`) 2/2 times inside the full test flow (after several prior page
interactions: navigation, tab click, several `text_content()`/`bounding_box()`
reads). A `expect(locator).to_be_focused()` check before typing did NOT fix
it — focus was confirmed `True` and the drop still happened.

## Fix

Switched to `.fill(query)` — already this codebase's established, working
pattern for exactly this input shape (`agents_list_page.py`'s
`search()`/`clear_search()` use `.fill()`, not `press_sequentially()`).
`.fill()` sets the value atomically in one `onChange` dispatch and reliably
triggered the component's search-filter behavior.

## When this applies vs. when it doesn't

- `mui-patterns.md`'s "never `fill()` on MUI form fields" warning targets
  TextFields/masked-input components where React's controlled-value sync
  genuinely requires real keyboard events. A bare `<Input onChange=...>`
  wrapping a native `<input>` (no formatting/masking) is a narrower case —
  check what the component actually does before defaulting to
  `press_sequentially()`; if a sibling page object already uses `.fill()` for
  the same input shape successfully, that's stronger evidence than the
  general rule.
- If you DO need `press_sequentially()` for a masked/validated field, don't
  assume the first char always lands — a focus check does not catch this;
  verify the final `input_value()` before trusting the state, or prefer a
  method that's already verified working (`agents_list_page.py`'s
  `verify_search_functional()` does the input_value check explicitly).

## Case

ELITEA-2312 (Users tab Activity table search-filter smoke check), PR #1189.
