---
name: Copying a suite-local helper must carry the machinery, not just the attribution
description: Diff the ancestor's body before shipping a copy — "lighter sibling" is how you reintroduce the race the ancestor exists to close.
type: feedback
aliases: [duplicated helper, suite-local helper, lighter sibling, _open_blank_composer, _poll_blank_state_holds, settle window, blank composer]
tags: [area/chat, area/implementation, type/gotcha]
created: 2026-08-29
updated: 2026-08-29
---

## What went wrong

This suite shares chat helpers by **per-file duplication with attribution**
(`_open_blank_conversation` -> `_open_genuinely_blank_conversation` ->
`_open_blank_composer`). I copied the ancestor for ELITEA-2390, decided my case
"needs less strictness", and wrote a **fixed `page.wait_for_timeout(1500)` + one
recheck** where the ancestor **polls**. Review blocked it (PR #1962).

The attribution line made it look like established shape. It was a regression of
the thing it cited.

## The invariant I got wrong

The SPA's last-viewed-conversation restore is **delayed**. The requirement is
that the blank state **HOLDS across a settle window** — not that it is true at
one instant. A fixed sleep followed by a single check samples the window **only
at its end**, so any restore that lands inside the window and is then superseded
reads as a blank composer.

Generalises past this helper: whenever the property is *"X stays true for N ms"*,
the shape is a poll that exits the moment X flips. `expect(...)` retry-until-true
has the wrong polarity — it proves X *becomes* true, never that it *stayed*.

`time.sleep` is fine as the poll interval here, unlike the WebSocket-frame case
in `.agents/testing.md`: each pass calls `chat.get_message_count()`, a Playwright
call, so the sync dispatcher stays pumped.

## The move

**Before shipping a copy, `git diff` the two bodies and ask what the ancestor's
extra machinery is FOR.** If you cannot name the failure it prevents, you are not
qualified to drop it. Pin the answer with a unit test that drives the real helper
against a fake page object on a virtual clock — the pre-fix shape must actually
fail it (verified by reverting the source, not assumed).

Related: [[teardown_restore_route_guard]]
