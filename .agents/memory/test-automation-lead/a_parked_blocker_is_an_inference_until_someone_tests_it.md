---
name: A parked blocker is an inference until someone tests it
description: ELITEA-2245..2248 sat parked for 11 waves on "needs multiple identities" — one live check disproved it; re-test a deferred assumption instead of re-deferring it
type: feedback
---

## What happened (#1398, settings-w12, 2026-08-30)

Four cases were held out of wave 1 with the reason *"they need a viewer/monitor identity and an
unauthenticated session — a different setup shape from anything the suite has built."*

That reason was written once, and then **I copied it forward in my own handover every single
session for eleven waves**, each time as though it were established fact. It was never tested.

Wave 12 finally dispatched it as a question rather than a constraint. The analyst found in one
live check that **roles are PROJECT-scoped**, and the shared test account already held three
distinct vantages: admin @ project 400, editor+viewer @ 399, viewer @ 471/406/25.

- ELITEA-2245 needed no second identity (the shared user IS admin on 400).
- ELITEA-2247 became a genuine 3-param spec across three real roles, each row asserting a
  different expected value.
- Only ELITEA-2248 was truly blocked, and for an unrelated reason (the Vite proxy sets the bearer
  token server-side, so no unauthenticated state exists on localhost).

Two of the four were automatable from day one.

## The mechanism to watch

A blocker written into a handover note **reads exactly like a verified finding** on the next
session's first pass. There is no marker distinguishing "we tried and it failed" from "we reasoned
that it would fail." Carried forward often enough, an inference becomes an institutional fact.

Worse, the deferral is self-reinforcing: every wave that skips the case adds evidence that skipping
is normal.

## What to do

- **When parking a case on a blocker, record HOW it was established** — "tested live, see AFS
  § Blocked Steps" vs "inferred from X, not tested." The second kind is a to-do, not a finding.
- **Re-test an untested blocker before re-deferring it.** One dispatch is cheap; eleven waves of
  deferral is not.
- **Put the assumption in the dispatch as a question, not a constraint.** The line that broke this
  open was literally *"the shared ${TEST_USER} is expected to already BE admin — verify that live
  before assuming a second identity is needed."* Phrasing it as a constraint would have produced
  another `blocked`.
- The failure is cheap to catch and expensive to keep: the analyst answered it in one session.

Related: [[put_durable_rules_in_canon_not_in_the_dispatch_prompt]] — same theme from the other
side: what you write down propagates, so be deliberate about whether it is fact or guess.
