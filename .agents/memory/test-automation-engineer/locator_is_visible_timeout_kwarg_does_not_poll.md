---
name: Locator.is_visible(timeout=) does not poll
description: Playwright Locator.is_visible(timeout=...) is a one-shot check — the timeout kwarg is deprecated/ignored; use .wait_for(state="visible", timeout=...) to actually wait
type: feedback
---

Confirmed against the installed `playwright` package's own docstring
(`.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py`,
`Locator.is_visible`): the `timeout` parameter is **deprecated and ignored** —
"`locator.is_visible()` does not wait for the element to become visible and
returns immediately." It's a pure current-state read, not a wait.

Hit this live on ELITEA-2368: `chat.answer_thought_accordion.is_visible(timeout=90_000)`
returned `False` almost instantly (test finished in ~22s, not ~90s) because the
"Thought for N secs" element genuinely didn't exist yet at the moment of the
call (right after clicking Send, before the AI started processing). Fix:
`chat.answer_thought_accordion.wait_for(state="visible", timeout=90_000)`.

**When `is_visible(timeout=...)` is still safe**: only when a REAL wait already
precedes it (a prior `expect_response`, `wait_for_page_load()`, another
`.wait_for()`/`is_agent_participant_in_composer()`-style method that itself
polls) — then it's a harmless one-shot read-after-wait. This is the existing
project convention throughout `automation/tests/ui/` (e.g.
`test_agent_hub_open_agent_detail_modal.py`) — don't "fix" those call sites,
they're correct as-is. Only add `.wait_for()` where the check is the FIRST
thing to observe a state transition, not a confirmation after one.

Same bug class: `assert chat.get_message_count() > initial_count` read
immediately after clicking Send can race the DOM commit and read the
pre-send count — use `chat.wait_for_message_count(initial_count + 1, timeout=...)`
first.
