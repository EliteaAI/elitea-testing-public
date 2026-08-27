---
name: Never accept a partial merge gate
description: A non-member failure mid-gate means re-gate from scratch — and check what the aborted run left behind
type: feedback
aliases: [2 of 3 gate, partial gate, re-gate, gate flake, closed set member]
tags: [area/merge-gate, type/discipline]
created: 2026-08-27
updated: 2026-08-27
---

## The situation

Gating ELITEA-2212 (sanctioned-RED, PR #1836): runs 1 and 2 produced the exact
closed-set signature. Run 3 produced something else entirely — a raw
`AssertionError` at the shared setup, 52 s against a ~125 s norm.

## The rule

**Re-gate from scratch. Do not accept 2-of-3.** `.agents/testing.md` § Merge
gate is explicit that any failure reaching the gate as a raw/uncaught exception
blocks — a failure outside the enumerated closed set is *by construction* not
the sanctioned signature. The temptation is real because two runs already
matched and each attempt costs ~6.5 min; the re-gate came back 3/3 immediately.

## The part that is easy to miss

**A discarded gate attempt still had side effects.** That same attempt's run 2
failed its guardrails-restore readback, leaving an ORG-WIDE flag set — and it
does not self-heal, because the fixture is read-mutate-restore: the *next* run
captures the polluted state as its own "original" and faithfully restores that.
Found it only because I checked the live config after discarding the attempt.

So: **bracket every gate run with a check of whatever shared state the module
mutates**, and verify that state is pristine after any aborted attempt. I ran
gate B with a `sensitive_tools` read before and after each of the 3 runs, which
turned "probably clean" into evidence for the closure record. Filed the fixture
hardening as its own issue (#1838) rather than folding it into the case PR —
the fixture is shared with three sibling cases and owes its own review.

## Before blaming the diff

Rule out the cheap explanations first, with evidence, and say which you ruled
out: the fixture's own SET-readback assertion had PASSED on the flaky run, so
the precondition was provably in place; the attach guard had passed too. What
remained was LLM trigger nondeterminism upstream of everything asserted. That
reasoning belongs in the known-noise ledger, not in a bug.

Related: [[sanctioned_red_tms_backwrite_shape]]
