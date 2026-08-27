---
name: Playwright sync API dispatches page events only inside a Playwright call
description: A time.sleep poll waiting on page.on(...) data never sees it — pump the driver or you get a false RED
type: feedback
aliases: [websocket frames not captured, framesent never fires, time.sleep poll starves playwright, capture_socketio_frames empty]
tags: [area/playwright, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

Playwright's **sync** Python API delivers page events (`websocket`, `framesent`,
`framereceived`, and by the same mechanism anything else fed by a callback) only
while the calling thread is **inside a Playwright call**. A poll loop built on
`time.sleep` therefore starves the dispatcher: the list your listener appends to
**cannot grow** for the whole duration of the poll.

## How it presents (measured 2026-08-27, ELITEA-2214)

Waiting up to 15 s for an outbound `chat_continue_predict` frame:

- with `time.sleep(0.25)` steps → list frozen at 18 entries, assertion failed
  with "the decision never left the browser" — **2 runs running**;
- the frame *and* its three `socket_validation_error` replies appeared
  **instantly** the moment any Playwright call ran (a stray `locator.count()` in
  a debug probe is what exposed it).

So the failure mode is a **false RED on a hard assertion**, blaming the product
for something the browser had already done. Nothing in the error distinguishes it
from a real product failure — the only tell is that the data shows up as soon as
you touch Playwright again.

## What to do

- Step the poll with `page.wait_for_timeout(...)` — it is the driver-pumping
  primitive, not a sleep standing in for a condition wait. In a project that bans
  `wait_for_timeout` (this one does), that is a **declared improvisation**: say so
  in the helper docstring and the Run Report.
- Or read the frames **after** a step that already waits on the page (a 60 s
  response wait pumps continuously, so everything is dispatched by then).
- The in-repo precedent already does this without saying why:
  `PipelineDetailPage.capture_websocket_frames()`'s usage example puts
  `page.wait_for_timeout(5000)` after its HITL click.

Shared collector now lives in `automation/utils/websocket_frames.py`.

Related: [[hitl_resume_is_rejected_not_silent]]
