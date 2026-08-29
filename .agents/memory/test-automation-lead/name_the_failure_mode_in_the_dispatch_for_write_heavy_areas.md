---
name: Name the failure mode in the dispatch when a sub-area is write-heavy
description: on write-heavy areas the danger is a spec that PASSES while leaving the environment altered — a red is the easy case; say so in the dispatch or the reviewer has no reason to look
type: feedback
---

## The pattern

On a write-heavy sub-area (create/edit/delete/set-default flows), the risk that actually
costs you is **not** a failing test. It is a test that goes green and leaves the environment
changed for everything after it — a deleted configuration, a moved default, a mutated org
setting. Nothing in the gate catches it: 3/3 green is exactly what it produces.

## What worked (settings-w10, 2026-08-30)

Before launching the wave I named the failure mode in the dispatch: *this is the second
write-heavy sub-area in a row; watch for a spec that passes while leaving the environment
altered.* Review then found precisely that — in `test_vector_storage_edit.py`,
`default_changed = True` was set **several statements after** the save it guards, so a flake
in the gap skips the teardown's default-restore while still deleting the configuration the
default pointed at. Fixed before merge.

The catch is attributable to the naming. A generic "review this PR" gives the reviewer no
reason to trace teardown-guard ordering against the operation it guards — the test reads fine
and passes either way.

## The rule

When the wave's sub-area mutates shared state, put the failure mode in the dispatch prompt in
words, not just the policy lines. Specifically ask for:

- every teardown guard flag set **immediately before** (never after) the mutation it guards;
- teardown restoring org/project-level defaults, not just deleting what the test created;
- what happens to the *next* spec if this one dies at each statement.

Related: [[sanctioned_red_is_never_back_written_automated]] (the other "green is not the
whole story" trap — a red that IS the correct outcome).
