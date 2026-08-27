---
name: SendMessage resume cannot be awaited in unattended mode
description: Resuming a subagent via SendMessage returns immediately and its reply arrives only as a task notification — unusable when the turn must not end
type: feedback
aliases: [SendMessage, resume subagent, background subagent, foreground dispatch, headless wait, Monitor trap]
tags: [area/orchestration, type/process]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

In unattended/factory mode the turn must never end with work in flight. `Agent(..., run_in_background: false)`
honours that: it blocks and returns the result in-turn.

**`SendMessage` does not.** It returns `{"success": true, "message": "Resuming agent ..."}` immediately.
The resumed agent's reply arrives later as a `<task-notification>` — i.e. only if the session is still
alive to receive it. There is no in-turn way to await it:

- foreground `sleep` is **blocked** by the harness ("use Monitor with an until-loop")
- `Monitor` is **session-fatal** in this mode (its "you will be notified, do not poll" contract holds
  only for live interactive sessions)

So a `SendMessage` follow-up is a bet that the notification lands before the turn ends. It is not a wait.

## What to do instead

Ask the follow-up question as a **fresh `Agent(run_in_background: false)` dispatch**, carrying the
established findings forward in the prompt as "take as given, do not re-derive". Costs a cold start;
buys a guaranteed in-turn result.

Reserve `SendMessage` for live interactive sessions, or for fire-and-forget where no reply is needed.

## Second-order cost, if you do it anyway

Both agents run **concurrently against the same live environment**. On 2026-08-27 (#1814) the resumed
analyst and the fresh analyst each created and deleted `autotest_*` agents in project 399 at the same
time, and each reported the other as "another actor is mutating this project" — noise in two otherwise
clean reports, plus ~190k tokens of duplicated investigation.

Corollary worth keeping on its own: **never have two ICs driving the same live project at once.** The
pipeline is serial by design for exactly this reason.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]]
