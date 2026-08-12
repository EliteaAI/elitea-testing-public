---
name: chat_page.py's two wait idioms coexist for different reasons; console+pageerror dual listener now established twice
description: chat_page.py has TWO valid "wait for async update" idioms that must not be conflated — a Playwright locator .filter(has_text=...) + .wait_for(state="visible") for simple text-equality waits (wait_for_message_count(), wait_for_context_budget_panel()), vs a manual time.monotonic() poll loop for waits that need Python-side logic like transient-message filtering (wait_for_generation_complete(), wait_for_message_content_stable()); picking the manual-loop idiom for a simple text-equality wait would itself be "inventing a new idiom" the skill forbids. Also: the console-only page.on("console", ...) side-channel listener misses uncaught JS exceptions — this is now a TWICE-confirmed gap (ELITEA-2094/PR#688, then independently rediscovered on ELITEA-2095/PR#693 round 2) — any new "no console errors" check in this repo should ship page.on("pageerror", ...) from the start, not as an afterthought fix.
type: feedback
---

## What happened

PR #693 (ELITEA-2095) round-2 review: a fresh reviewer independently re-ran the
merged spec live 5x (didn't trust the prior "GREEN 3/3" Run Report) and got
2/5 FAILED — two real races the implementer's own local runs never caught.

**Finding A** — `get_context_budget_messages_count()` /
`get_context_budget_summaries_count()` (`chat_page.py`) did a one-shot
`.text_content()` read immediately after `wait_for_context_budget_panel()`,
which only waits for the panel *heading*, not for the Messages/Summaries rows
to reflect the updated value. Reproduced: assertion `got: '0'`, failure
screenshot captured moments later already showed `Messages: 4` rendered — a
genuine async-update race, not flaky infra.

**Finding B** — the test had `wait_for_generation_complete()` correctly
placed before Step 2 (with its own inline comment explaining exactly why
`wait_for_message_content_stable()` alone isn't authoritative — the app's
internal streaming/nav-blocking flag can trail the text heuristic), but was
missing the *identical* guard after the FIRST message's response. The
pattern existed once in the file and needed to be applied symmetrically.

**Secondary** — the round-1 fix (same PR, earlier commit) wired
`page.on("console", ...)` for the "no side-channel errors" check, but missed
`page.on("pageerror", ...)`. This is the SAME gap already discovered and
fixed same-day on sibling PR #688/ELITEA-2094 — i.e. it recurred within the
same day across two parallel PRs because the round-1 fix here didn't check
for the sibling PR's precedent before shipping.

## The generalizable fact — two wait idioms, don't conflate them

`chat_page.py` has two DIFFERENT valid patterns for "wait for an async DOM
update," and choosing the wrong one for the situation is itself a form of
"inventing a new idiom":

1. **Playwright-native locator wait** — construct a locator (optionally
   `.filter(has_text=...)`) and call `.wait_for(state="visible", timeout=...)`.
   Used by `wait_for_message_count()`, `wait_for_context_budget_panel()`, and
   now `wait_for_context_budget_messages_count()`/
   `wait_for_context_budget_summaries_count()` (added this round). Use this
   when the condition is expressible as "does this element/text exist,"
   nothing more.

2. **Manual `time.monotonic()` poll loop** — used by
   `wait_for_generation_complete()` (polls for a specific button becoming
   visible via a hand-rolled loop, not a locator wait, because it also needs
   to swallow transient DOM-detach exceptions during re-render) and
   `wait_for_message_content_stable()` (needs Python-side logic — comparing
   successive text reads, filtering `TRANSIENT_MESSAGES` like "Thinking…" —
   that a pure locator wait can't express).

When adding a new async-update wait, match the SHAPE of the condition to the
existing idiom that already solves that shape, rather than defaulting to
whichever one you saw most recently. A reviewer explicitly named which two
existing methods to imitate (`wait_for_message_count()` /
`wait_for_context_budget_panel()`) — that pointer was itself the signal for
which idiom family applied here (locator-wait, not poll-loop).

## The generalizable fact — dual console+pageerror listener is now the default, not an exception

Two independent PRs (ELITEA-2094/#688, ELITEA-2095/#693) both shipped a
console-only side-channel check first, then had to retrofit
`page.on("pageerror", ...)` after the fact. The dual-listener pattern should
now be treated as the REPO DEFAULT for any new "no unexpected console/JS
errors" check, not something to add only when a reviewer points it out a
second time:

```python
console_messages = []
page_errors: list[str] = []

def _on_console(msg):
    if msg.type == "error" and not _is_known_<...>(msg):
        console_messages.append(msg)

def _on_pageerror(exc):
    page_errors.append(str(exc))

page.on("console", _on_console)
page.on("pageerror", _on_pageerror)
...
assert not console_messages and not page_errors, (...)
```

## Verification technique reused this round

Before editing `get_context_budget_messages_count()`/
`get_context_budget_summaries_count()`, confirmed via
`git diff origin/automation/base -- automation/pages/chat_page.py | grep -n "context_budget_..._count"`
that these two methods were BRAND NEW in this PR with a SINGLE caller (the
test itself) — so editing/extending them freely carried zero shared-caller
regression risk, despite `chat_page.py` overall having ≥3 merged callers
elsewhere (the file-level threshold doesn't apply per-method; check the
specific method's own caller count before assuming the additive-only
constraint bites).
