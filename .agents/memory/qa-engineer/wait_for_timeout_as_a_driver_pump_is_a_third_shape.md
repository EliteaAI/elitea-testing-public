---
name: wait_for_timeout as a DRIVER PUMP is a third shape — time.sleep there causes a FALSE RED
description: Playwright's sync API dispatches page/ws events only inside a Playwright call; a time.sleep poll freezes the frame list, so the pump is load-bearing infrastructure, not a banned sleep
type: feedback
aliases: [driver pump, wait_for_timeout pump, framesent not dispatching, websocket frames frozen, sync api event dispatch]
tags: [area/review, type/canon-gap]
created: 2026-08-27
updated: 2026-08-27
---

## The three shapes of `page.wait_for_timeout` a reviewer meets

`.agents/conventions.md` bans `sleep`/`wait_for_timeout` outright. Two shapes were
already distinguished in memory; ELITEA-2214 (PR for `tests/ELITEA-2214-block-with-comment-rework`)
adds a third that neither test covers.

| Shape | Tell | Disposition |
|---|---|---|
| **Copied habit** — a sleep standing in for a condition wait that DOES exist | no defect link, no declaration, DOM signal available | violation → `CHANGES_REQUESTED` ([[wait_for_timeout_copied_despite_afs_warning]]) |
| **Defect workaround** — no DOM/network signal exists because of an OPEN product bug | filed defect + stated reason + declared in the diff | sanctioned declared improvisation ([[declared_wait_for_timeout_vs_copied_habit]]) |
| **Driver pump** (this entry) — the wait exists to yield to Playwright's driver so events dispatch at all | the oracle is an in-process list fed by a Playwright *event callback*, not a locator | infrastructure necessity; `time.sleep` there is the bug |

## Why the pump is load-bearing

Playwright's **sync** API dispatches page events (`websocket`, `framesent`,
`framereceived`, `console`, `pageerror`) only while the calling thread is inside a
Playwright call — the greenlet only pumps the driver when you re-enter it. A
`time.sleep` poll therefore **starves the dispatcher**: measured 2026-08-27 on
ELITEA-2214, the captured frame list stayed frozen at 18 entries for a full 15 s and
every queued frame arrived at once on the next Playwright call.

The consequence is not a slow test, it is a **false RED on a hard row**: the spec
reported "the decision never left the browser" while the browser had in fact sent it.
`page.wait_for_timeout(...)` is the documented way to yield to the driver.

## The reviewer move

When a diff polls for something that is NOT a locator — a websocket frame list, a
console-message list, any list fed by `page.on(...)` — the poll step **must** be a
Playwright call. Ask instead:

1. Is the poll **bounded** by a deadline and does it **exit early** on the condition?
2. Does it return the observed evidence rather than a boolean, so the CALLER asserts?
   (A helper that decides pass/fail hides what was seen.)
3. Is the pump declared in the diff itself (docstring/comment), not only in the AFS?

All three → non-blocking, and the canon gap belongs on a `question` card
(ELITEA-2214 filed #1842) rather than in the verdict.

Related: [[declared_wait_for_timeout_vs_copied_habit]] · [[wait_for_timeout_copied_despite_afs_warning]] · [[chat_turn_dies_silently_read_the_socketio_frames]] · [[assertions_behind_a_failing_wait_are_never_evaluated]]
