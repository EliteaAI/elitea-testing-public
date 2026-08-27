---
name: A failure card's "deployed-env-only" claim is a hypothesis, not a finding
description: Reproduce locally first — a CI-only failure that reproduces 3/3 on localhost is deterministic, and determinism is itself diagnostic
type: feedback
aliases: [deployed only failure, dev.elitea.ai only, CI-only red, reproduce locally first, env issue classification]
tags: [area/triage, type/diagnosis]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`[Fix][ELITEA-…]` cards generated from a GHA failure name the environment the failure was
*observed* in (e.g. "Environment: dev.elitea.ai") and often suggest *race condition* or
*env issue* among the possible causes. It is tempting to route the analyst straight at the
deployed env to "reproduce where it failed".

Don't. **Reproduce on `localhost:5173` first** — the project's canonical loop — and treat the
deployed-only framing as unverified. On #1872 (ELITEA-1888) the card asserted a dev-only
failure; it reproduced **3/3 on localhost**, byte-identical signature.

## Why the outcome is worth more than the reproduction

The *shape* of the reproduction classifies the bug for free:

- **Reproduces deterministically anywhere** ⇒ it is a structural defect (a stale read, a
  wrong wait, a dead predicate), not an env artifact. Chasing the deployed env would have
  cost a slow run and taught nothing.
- **Reproduces only sometimes, or only on the deployed env** ⇒ *then* it is genuinely
  timing/env-sensitive, and the deployed run is worth its cost.

A race that the test "used to win and now loses structurally" looks exactly like an env issue
in a CI log and exactly like a code defect on localhost. Only running it locally separates them.

## Dispatch phrasing that works

Tell the analyst: localhost is primary; **if it does not reproduce there, that is itself
evidence**, and they may then run against the deployed env to confirm. Ask for target +
run counts + verbatim results, so the classification rests on observation rather than on
the card's opening paragraph.

Related: [[promoted_test_fixes_branch_from_main]]
