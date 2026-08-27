---
name: A docs-only correction must fix the strings a reader sees at FAILURE time
description: When reviewing a "documentation correction" PR, grep the module's runtime failure/assertion messages too — docstrings get corrected, message literals get forgotten.
type: feedback
aliases: [docs-only PR review, superseded docstring, gate marker scope, pytest.fail message, GATE_EXCLUDED_REASON]
tags: [area/merge-gate, type/review]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

PR #1844 corrected a superseded characterisation of known defect #1127 across
the module docstring, the class docstring, the gate marker and the AFS — and
left the `pytest.fail()` message that fires when the defect actually hits still
reading *"Non-deterministic known defect observed this run"*. That string is the
**only** one a gate owner reads at the moment it matters, and it said the exact
opposite of the PR's new ruling ("a red on this node id is NOT sanctioned —
treat it as a blocker").

Docstrings are what the author is editing; message literals are what the reader
is reading. A correction that touches only the former ships the old claim into
the operationally decisive spot.

## The habit

On any "docs-only" / re-classification PR, grep the touched module for
reader-facing strings, not just docstrings:

```bash
grep -nE '(pytest\.fail|raise AssertionError|assert .*,)' <module> | grep -iE 'known defect|non-determin|flaky|expected|sanctioned'
```

Then ask of each hit: if this fires tomorrow, does it tell the reader what the
PR now says, or what the PR just superseded?

## Two companion techniques from the same review

- **Prove "no behavioural change" mechanically.** Parse both revisions, strip
  every docstring from the AST, and compare the dumps — the residue is exactly
  the executable delta. On #1844 that was one string constant, in one command,
  with no line-by-line trust required.
- **A rescoped greppable marker is only rescoped if the GREP is clean.** Run the
  repo-wide grep the marker advertises. #1844's still hit a sibling AFS
  (`lcovered_*_ELITEA-2474.md`) asserting the superseded module-wide exclusion,
  so the "a grep cannot mislead a gate owner" claim was not yet true.

Related: [[known_defect_determinism_can_be_tool_dependent]]
