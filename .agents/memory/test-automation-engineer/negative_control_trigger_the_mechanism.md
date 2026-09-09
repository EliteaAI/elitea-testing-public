---
name: For a bursty intermittent defect, trigger the mechanism — don't wait on the lottery
description: Waiting for a ~25% condition to recur burns runs; inducing the real mechanism honestly is faster and just as valid
type: feedback
aliases: [negative control, intermittent repro, bursty flake control]
tags: [type/technique]
created: 2026-09-10
updated: 2026-09-10
---

Demonstrating that a repaired spec reports better than the old one requires the
failure condition to be PRESENT. When that condition is intermittent and
bursty, waiting for it is a lottery: on ELITEA-2453 the condition was measured
at ~25% overall, yet it did not appear once in **9 consecutive effective runs**
of the pre-repair spec (~15 min of wall clock, and no bound on how much more).

The cheap, still-honest move is to **trigger the real mechanism deliberately**
rather than wait for it or fake it. The defect was "an LLM answering in prose
instead of JSON causes a silent no-op state write", so swapping the fixture's
system prompt for one that genuinely invites prose reproduced it **first try**.

The line that matters: nothing was mocked, routed, fulfilled or fabricated — a
real model produced a real prose answer and the real backend really wrote no
state. That is inducing the condition, not simulating it, and it stays inside
the fidelity policy. Fabricating a frame or monkeypatching the state would NOT
have been, and would have proved nothing.

Two obligations when doing this:
- Say plainly that the induced trigger differs from the natural one, and keep
  any naturally-occurring occurrence as the primary evidence.
- Check whether the induced variant reproduces the SAME sub-shape. Here it did
  not exactly: the induced run left `custom_text` absent (panel rendered ``)
  while CI's occurrence had it present-but-empty (panel rendered `""`), so the
  old spec died one assertion earlier. Same fault, different line — report it.
