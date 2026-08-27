---
name: Re-check a card's blocker before assuming it still blocks
description: A parked card's blocker is often already dead — the precondition moved, not the defect fixed; verify before re-parking
type: feedback
aliases: [blocked card, unpark, stale blocker, waiting on, re-park]
tags: [area/orchestration, type/convention]
created: 2026-08-27
updated: 2026-08-27
---

## What happened

#416 (ELITEA-2213) sat `Blocked — Waiting on #1140` from 2026-08-04. #1140 is
still **OPEN** — and was never going to close, because it tracks an Admin UI
route that localhost does not serve at all. The card unblocked anyway: a sibling
delivery (#415) moved the guardrails precondition off the Admin UI onto the
config REST endpoint (`PUT {api}/admin/plugin_config_values/administration/guardrails`),
so the dependency simply stopped existing.

**An open blocker issue is not evidence the card is still blocked.** The question
is whether the *dependency* still holds, not whether the *issue* closed. Ways a
blocker dies without closing: the precondition is reached by another route, the
case is re-scoped, a sibling delivery builds the fixture, the surface moves.

## The move

On picking up any `Blocked` card, before anything else: read the blocker's own
thread **and** the sibling cards' recent comments. On #416 the answer was sitting
in a heads-up comment left by #415's lead — including the two open product defects
that would land on this case and the exact assertion to distrust. Reading it first
saved the whole discovery pass.

Corollary going the other way: when you park or deliver a card, **leave the
heads-up on the sibling cards**. It is the cheapest handoff in the pipeline and it
is what unblocked this one.

Related: [[assertions_behind_a_failing_step_never_ran]] · [[loop_redispatch_on_terminal_ready_card_can_false_positive_block]]
