---
name: An orchestrator's dispatch premise can be FALSE — build the refusal path in
description: My brief asserted a source fact that was wrong and would have shipped a double-send; the implementer falsified it instead of complying, and the reviewer backed him
type: feedback
aliases: [wrong dispatch premise, IC refused the brief, orchestrator error, verify my own claims, declared deviation upward]
tags: [area/orchestration, type/gotcha]
created: 2026-09-04
updated: 2026-09-04
---

## What happened (ELITEA-1886 / #1812, round 2)

I briefed a bounded retry keyed on *"a still-populated composer proves nothing was sent —
`sendQuestion()` clears it synchronously and `ChatBox.jsx` does not override it"*, inherited
from the analyst and **stated as verified source fact**.

It was false:

```
ChatBox.jsx:2950   clearInputAfterSubmit={false}
ChatBox.jsx:2127   // Chat passes clearInputAfterSubmit={false}, so clearing is the caller's job
```

Clearing happens at `ChatBox.jsx:1174`, after `await onSend(...)` and
`await uploadAttachments(...)`, success path only. So a populated composer is a **lagging**
signal — equally consistent with "nothing sent" and "send in flight whose POST hasn't
returned". **The design I ordered would have fired a second send on a message the backend
already had.**

The implementer refused to build on it, said so, and built a **request-keyed** discriminator
instead (`page.on("request")`; `sendQuestion()` early-returns before any network call, so an
issued request proves the send registered). He kept my composer check as a second condition —
a conjunction, so it retries strictly *less* often than I asked for. The reviewer verified
independently and wrote: *"I'd have blocked the version you briefed."*

## Why this is a standing hazard, not a one-off

Role-overrides § Orchestrator already says my dispatch prompt is the strongest signal in the
pipeline: an IC treats it as settled, and the reviewer ends up judging work *I ordered*,
which removes the last independent axis. That rule is written about *techniques* I
prescribe. **It applies just as hard to FACTS I assert.** A false premise stated
confidently propagates through analyst → implementer → reviewer and can pass every gate,
because all three artifacts agree.

## What to do

- **Attribute claims in the dispatch.** Say "the analyst reports X (I have not verified it)"
  rather than laundering it into "X". I wrote it as established fact and it was not.
- **Explicitly license refusal.** Dispatches should say: *if a premise here is wrong, falsify
  it and tell me — do not build on it.* It cost nothing and it is what saved this round.
- **Verify a load-bearing source claim myself before it becomes a design constraint** — this
  was one `grep` (`grep -rn clearInputAfterSubmit src/`) and it settled the matter.
- **When it turns out I published the false premise, correct the public record.** I had
  filed product bug #2011 on it; I posted a correction and retitled the issue. An
  appropriately-hedged open report beats a confident wrong one, and beats deleting the lead.
- **In the reviewer dispatch, name the deviation and ask them to adjudicate it on merits** —
  including "tell me if my original brief was right". Getting corrected twice is cheaper than
  shipping a double-send.

Related: [[a_delivered_card_is_not_verified_until_the_env_ran_it]]
