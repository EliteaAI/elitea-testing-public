---
name: Put a durable rule in canon, not in the dispatch prompt
description: the batch workflow has no lead-notes arg — smuggling guidance into case titles works once; writing it into .agents/*.md reaches every slot of every future wave through the @-import
type: feedback
---

## The situation

`batch-build.workflow.mjs` accepts no free-text guidance channel. The only per-case string that
reaches a slot is `title`. So when a wave needs a warning ("this sub-area is write-heavy"), the
tempting move is to append it to each case title.

## Why that is the wrong instinct

A title-smuggled warning applies to exactly one wave, is invisible to anyone reading the repo, and
disappears the moment the batch closes. Worse, it reads as noise in every artifact that quotes the
title afterwards (report rows, PR bodies, closure records).

## What works instead

Write the rule into `.agents/testing.md` (or the relevant `.agents/*.md`) and push it to
`automation/base` **before launching the wave**. This project `@`-imports the whole `.agents/`
block from CLAUDE.md, so the rule reaches analyst, implementer, reviewer and gate — on this wave
and every future one, on this card and every other card.

## Worked proof, one day apart (2026-08-29 -> 30)

- **w10**: review caught a teardown-guard ordering bug (`default_changed = True` set AFTER the save
  it guards — a spec that PASSES while leaving damage; the N-green gate structurally cannot catch it).
- I wrote it up as `.agents/testing.md` § *Teardown-guard ordering on write-heavy specs* and pushed
  it before launching w11.
- **w11**: the reviewer applied that section unprompted and blocked ELITEA-2416 for the same class —
  a conversation id captured AFTER the assertions that could orphan it. Fixed, then pinned by a unit
  test so it cannot silently regress.

The rule caught a second instance within hours of being written, in a unit I had not flagged.

## The test to apply

Ask: *will this still be true next wave?* If yes, it is canon — spend the ten minutes. If it is
genuinely wave-local (which case ids cluster together, which project id to use), the title/args are
the right place.

Related: [[name_the_failure_mode_in_the_dispatch_for_write_heavy_areas]] — the w10 lesson this
supersedes in mechanism: name the failure mode, but name it in CANON, not in the prompt.
