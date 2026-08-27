---
name: Supersession sweep must follow the marker's own grep
description: A doc-correction PR is incomplete until every hit of the mechanical marker's documented grep is superseded, not just the one the prior review named.
type: feedback
aliases: [GATE_EXCLUDED_REASON grep, stale cross-reference, supersession sweep, docs-only PR review, gate marker scope]
tags: [area/review, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The gotcha

When a module carries a **mechanical marker** whose documented use is "grep the
repo for `<CONST>` when composing the gate", that grep IS the marker's contract
surface. A PR that rescopes the marker must supersede **every** file the grep
returns — otherwise a gate owner following the documented procedure lands on a
stale sibling doc and is told the opposite of what the corrected constant says.

Worked case, ELITEA-2215 / PR #1844 (fix round 1). The rescope of
`GATE_EXCLUDED_REASON` from module-wide to one node id was correct in the module
and in the AFS, and the `lcovered_..._ELITEA-2474.md` hit got an explicit
"Superseded in part" note. But `lextend_..._ELITEA-2210.md:247-249` — a hit of
the same grep — still read *"**Both** the existing covering test AND the new
… test are excluded … (non-deterministic known defect #1127, see
`GATE_EXCLUDED_REASON`)"*, with no supersession marker. One sibling swept, one
missed; the mis-steer survived at the exact address the procedure sends you to.

**Review move:** run the marker's own grep and tick off *every* hit against the
corrected claim. A prior review naming one stale hit is not the enumeration —
re-run it yourself.

## Its twin: "has not fired" is a lifetime claim

Same PR: the corrected constant dropped the flagged "tool-dependent" causation
but replaced it with `"#1127 has not fired on this trigger"` — undated,
present-perfect, and contradicted by the same file's own round-1 record (the
2026-08-03 leak block was a literal `<invoke name="create_file">`). When a
document has explicitly ruled that **no per-tool lifetime figure is claimable**,
"never fired" is that same forbidden claim in its strongest form. Scope such a
clause to the measurement window ("did not fire in any of those 14 runs") or
drop it. Strings that travel alone — a constant a gate owner reads out of
context — get the strictest reading, not the charitable one.

Related: [[docs_only_corrections_must_fix_runtime_messages]]
