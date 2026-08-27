---
name: A "non-deterministic" known defect may actually be trigger-dependent
description: Re-measure a defect per TRIGGER before blocking a case on it — one aggregate rate can hide two deterministic populations
type: feedback
aliases: [non-deterministic defect, flaky defect rate, 1127, tool-dependent defect, blocked on known defect]
tags: [area/chat, type/classification]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`elitea-testing-public#1127` (direct toolkit call narrates instead of executing) was
recorded as *non-deterministic, 2/5* and ELITEA-2215 was downgraded
`ready-for-automation` → `blocked` on exactly that number: a probabilistic defect
satisfies neither the plain green gate nor `.agents/testing.md` § Merge gate's
sanctioned-RED "deterministic 3/3" bar.

The 2/5 was an **aggregate across two different triggers**. Measured per-trigger
(2026-08-27, all `--reruns 0`, separate invocations, backend-verified via
`ArtifactAPI`):

- `create_file` — 5/5 GREEN (11/11 counting the lead's same-day runs)
- `delete_file` — 0/2 GREEN, 7/7 RED lifetime, byte-identical signature

Two deterministic populations, not one random one. The case was unblocked on a plain
green gate; the sibling case stayed sanctioned-RED.

## The habit

Before blocking a case on "the defect is flaky", ask **flaky across what?** Split the
runs by trigger (tool, endpoint, entity type, user role) and re-measure each population
separately. A rate is only meaningful over a fixed trigger.

Two guards that made this safe to act on:

- **A green must be backend-verified.** The module classifies each run against
  `ArtifactAPI` ground truth, so a green provably means the tool really ran — a
  DOM-only green would have proved nothing.
- **State the confound.** The two classes differed in message wording and preconditions
  too, so "tool-dependent" is the best-supported discriminator, not a root cause. Say
  that in the AFS instead of smoothing it over.

Related: [[project_briefing]]
