---
name: Capture the real payload — an inferred one gets refuted
description: Patterns derived from a nearby channel (LLM prose, a sibling toolkit) look right and are wrong; make the analyst capture the actual payload before an oracle ships
type: feedback
aliases: [inferred pattern, oracle regex, payload shape, tool_output, capture probe, sample provenance]
tags: [area/test-repair, type/fidelity]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

An oracle that matches a payload shape must be built from a **captured** payload. A shape
inferred from an adjacent channel is confident, plausible, and wrong often enough to matter
— and it fails in the worst way: it re-creates the very false-RED you were repairing, one
layer down, where nobody is looking for it.

## Two refutations in one card — ELITEA-1140 / #1817 (2026-08-27)

1. **github.** Pass 1 could not capture the success payload (expired PAT, #1673) and
   inferred `^Branches in \S+:` from the **CI chat message**. Pass 2 captured the real
   `tool_output` via an anonymous-auth credential: it is a **JSON array**
   (`[{"name": …, "protected": false}, …]`). `Branches in …:` was LLM *narration* — which
   even miscounted ("Total: 102" for 100 entries). The inferred pattern would have
   red-failed CI on a genuine success.
2. **confluence.** *I* then assumed the failure shape was `Failed to list pages: 401 …`, by
   analogy with github, and put that in the dispatch. Confluence actually returns a prose
   block (`Tool execution error!\n\nPossible root causes: …`). The implementer captured it
   instead of trusting me. Had they not, the pattern would have been wrong about the exact
   payload it exists to reject.

## Orchestrator moves that make this cheap

- **Name the observable and the constraint; never hand down a shape.** My analogy became a
  near-miss precisely because a dispatch prompt reads as settled to an IC.
- When a credential blocks capture, look for an **honest alternative producer** before
  accepting inference — anonymous auth against a public resource produced a real
  success here, and it is not a substitution because the system still produced every byte.
- Reading a *captured* payload back in a unit test is fine; **authoring** one is a fidelity
  violation. Store whole frames rather than loose extracts, so a sample cannot drift from
  its source.
- Provenance is checkable: byte-length/content match against the source, cross-checking
  identifiers against live ground truth, and — a reviewer's trick worth stealing —
  decoding **UUIDv7** `run_id`s, whose first 48 bits are a creation timestamp, and
  confirming they agree sub-millisecond with a separately-serialized `timestamp` field.
  A hand-written dict cannot fake that.

Related: [[removing_a_false_red_guard_can_create_a_false_green]]
