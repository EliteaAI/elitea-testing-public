---
name: Guard-dominated equality oracle — how to check it for vacuity
description: An oracle-equality assertion is non-vacuous only if a guard rejects the empty/default shape AND dominates every step that reads it
type: feedback
aliases: [vacuous equality, wire oracle vacuity, backend_state equality, precondition guard domination]
tags: [area/review, type/trap]
created: 2026-09-10
updated: 2026-09-10
---

## The trap

The fidelity policy's prescribed cure for a nondeterministic producer — *capture the real
response and assert the UI against it* — swaps a content premise (`!= '""'`, `len(x) > 0`)
for an equality (`json.loads(rendered) == backend_state[name]`). Equality between two
things that are BOTH empty passes and proves nothing. `"" == ""`, `[] == []`, `{} == {}`.

So an oracle-equality repair is only as strong as its precondition guard. Three checks,
in this order:

1. **Does the guard reject the default/empty shape?** Not "is the key present" — the
   default IS a present key with an empty value. It must assert non-empty per type.
2. **Does the guard DOMINATE every step that reads the oracle?** Trace the control flow:
   the only exits from the guard loop must be (a) `break` on guard-true and (b) a hard
   failure. A `continue`, a soft-assert, a skip, or a step that reads the oracle from
   *inside* the loop breaks domination and re-opens the vacuum.
3. **Are the pre-repair assertions ENTAILED by guard + equality?** If yes, nothing was
   weakened and the repair is strictly stronger. If any removed assertion is not entailed,
   coverage was dropped, whatever the AFS says.

## The type-check gap that survives all three

`isinstance(x, (int, float))` is **True for `bool`** — `bool` subclasses `int` in Python.
A guard written that way accepts `custom_num: true`, and the downstream "renders as a bare
JSON number" shape assertion accepts `"true"` as well (not quoted, parses, isinstance-int).
A numeric-type guard needs `and not isinstance(x, bool)`.

Related: [[pipeline_run_state_wire_oracle]]
